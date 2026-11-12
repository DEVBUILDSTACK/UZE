"""Solana devnet settlement for the composition layer (Sprint 1.5).

Executes the payment leg of a Match: a USDC transfer on Solana
devnet from the marketplace operator's Chain-Signature-derived
address to the winning bidder's derived address, signed by NEAR's
MPC network (chain_sig.mpc_sign) — no Solana private key exists
anywhere in this system; the NEAR identity is the signer.

Outcome states, stated honestly (the endpoint maps them onto the
Diagram 4 lifecycle; nothing here claims a settlement that did not
confirm on-chain):

  settled — broadcast and confirmed on devnet; solanaTx is the
            transaction signature.
  signed  — the transfer was fully built and MPC-signed over the
            exact message bytes, but NOT broadcast: the payer is
            underfunded (checked on-chain first). This is the
            dry-run state while devnet funds are pending — real
            signature, no broadcast, never reported as settled.
  failed  — broadcast attempted and the chain rejected it, or the
            confirmation window elapsed.

RPC transport is aiohttp with trust_env — the same egress-proxy fix
as near_client (this VM's direct TLS is intercepted).
"""

from __future__ import annotations

import asyncio
import base64
import json

import chain_sig

DEVNET_RPC = "https://api.devnet.solana.com"
USDC_MINT_DEVNET = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
USDC_DECIMALS = 6
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
ATA_PROGRAM = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
SYSTEM_PROGRAM = "11111111111111111111111111111111"

# The marketplace operator identity whose derived address pays. In
# the full design the poster funds settlement; for Sprint 1.5 the
# operator account (the contract account) is the settlement signer —
# its derivation is the one proven on 2026-11-07.
OPERATOR_ACCOUNT = "uzemarkets-talent.testnet"


def ata_address(owner: str, mint: str = USDC_MINT_DEVNET) -> str:
    from solders.pubkey import Pubkey

    ata, _ = Pubkey.find_program_address(
        [
            bytes(Pubkey.from_string(owner)),
            bytes(Pubkey.from_string(TOKEN_PROGRAM)),
            bytes(Pubkey.from_string(mint)),
        ],
        Pubkey.from_string(ATA_PROGRAM),
    )
    return str(ata)


async def _rpc(session, method: str, params: list):
    async with session.post(
        DEVNET_RPC,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
    ) as resp:
        body = await resp.json()
    if "error" in body:
        raise RuntimeError(f"{method}: {body['error'].get('message')}")
    return body["result"]


async def _settle_usdc_async(
    payee_predecessor: str, amount_usdc: int, path: str = ""
) -> dict:
    import aiohttp
    from solders.hash import Hash
    from solders.instruction import AccountMeta, Instruction
    from solders.message import Message
    from solders.pubkey import Pubkey

    payer_address, _ = chain_sig.derive_address(OPERATOR_ACCOUNT, path)
    payee_address, _ = chain_sig.derive_address(payee_predecessor, path)
    payer_ata = ata_address(payer_address)
    payee_ata = ata_address(payee_address)
    base_units = amount_usdc * (10**USDC_DECIMALS)

    outcome = {
        "payerAddress": payer_address,
        "payeeAddress": payee_address,
        "payerNearAccount": OPERATOR_ACCOUNT,
        "payeeNearAccount": payee_predecessor,
        "amountUsdc": amount_usdc,
        "mint": USDC_MINT_DEVNET,
        "solanaTx": None,
    }

    async with aiohttp.ClientSession(trust_env=True) as session:
        # Fund checks first — they decide signed vs settled.
        sol = await _rpc(session, "getBalance", [payer_address])
        payer_sol = sol["value"]
        try:
            bal = await _rpc(session, "getTokenAccountBalance", [payer_ata])
            payer_usdc = int(bal["value"]["amount"])
        except RuntimeError:
            payer_usdc = 0  # ATA does not exist yet
        funded = payer_sol >= 10_000 and payer_usdc >= base_units

        payee_ata_info = await _rpc(
            session, "getAccountInfo", [payee_ata, {"encoding": "base64"}]
        )
        instructions = []
        if payee_ata_info["value"] is None:
            instructions.append(
                Instruction(
                    program_id=Pubkey.from_string(ATA_PROGRAM),
                    accounts=[
                        AccountMeta(Pubkey.from_string(payer_address), True, True),
                        AccountMeta(Pubkey.from_string(payee_ata), False, True),
                        AccountMeta(Pubkey.from_string(payee_address), False, False),
                        AccountMeta(Pubkey.from_string(USDC_MINT_DEVNET), False, False),
                        AccountMeta(Pubkey.from_string(SYSTEM_PROGRAM), False, False),
                        AccountMeta(Pubkey.from_string(TOKEN_PROGRAM), False, False),
                    ],
                    data=bytes([1]),  # CreateIdempotent
                )
            )
        instructions.append(
            Instruction(
                program_id=Pubkey.from_string(TOKEN_PROGRAM),
                accounts=[
                    AccountMeta(Pubkey.from_string(payer_ata), False, True),
                    AccountMeta(Pubkey.from_string(USDC_MINT_DEVNET), False, False),
                    AccountMeta(Pubkey.from_string(payee_ata), False, True),
                    AccountMeta(Pubkey.from_string(payer_address), True, False),
                ],
                data=bytes([12])
                + base_units.to_bytes(8, "little")
                + bytes([USDC_DECIMALS]),  # TransferChecked
            )
        )
        blockhash = (await _rpc(session, "getLatestBlockhash", []))["value"][
            "blockhash"
        ]
        message = Message.new_with_blockhash(
            instructions,
            Pubkey.from_string(payer_address),
            Hash.from_string(blockhash),
        )
        message_bytes = bytes(message)

        signature = await chain_sig._mpc_sign(OPERATOR_ACCOUNT, message_bytes, path)
        wire = b"\x01" + signature + message_bytes

        if not funded:
            outcome["status"] = "signed"
            outcome["reason"] = (
                f"payer underfunded: {payer_sol} lamports SOL, "
                f"{payer_usdc} USDC base units; needs >=10000 lamports "
                f"and {base_units} base units. Signed, not broadcast."
            )
            return outcome

        sent = await _rpc(
            session,
            "sendTransaction",
            [
                base64.b64encode(wire).decode(),
                {"encoding": "base64", "preflightCommitment": "confirmed"},
            ],
        )
        tx_sig = sent if isinstance(sent, str) else sent.get("result", sent)
        outcome["solanaTx"] = tx_sig
        for _ in range(30):
            statuses = await _rpc(
                session, "getSignatureStatuses", [[tx_sig]]
            )
            entry = statuses["value"][0]
            if entry is not None:
                if entry.get("err"):
                    outcome["status"] = "failed"
                    outcome["reason"] = f"on-chain error: {entry['err']}"
                    return outcome
                if entry.get("confirmationStatus") in ("confirmed", "finalized"):
                    outcome["status"] = "settled"
                    return outcome
            await asyncio.sleep(2)
        outcome["status"] = "failed"
        outcome["reason"] = "confirmation window elapsed (60s)"
        return outcome


def settle_usdc(payee_predecessor: str, amount_usdc: int, path: str = "") -> dict:
    """One settlement outcome, as documented in the module docstring.
    Never raises for chain conditions — the outcome carries them;
    raises only for local construction errors."""
    try:
        return asyncio.run(
            _settle_usdc_async(payee_predecessor, amount_usdc, path)
        )
    except Exception as exc:
        return {
            "status": "failed",
            "reason": f"{type(exc).__name__}: {exc}",
            "payeeNearAccount": payee_predecessor,
            "amountUsdc": amount_usdc,
            "solanaTx": None,
        }
