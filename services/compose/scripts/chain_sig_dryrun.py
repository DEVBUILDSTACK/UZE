"""Chain Signatures dry run — the Day 1 go/no-go, retried per
DeepSeek's Nov 8 directive (attempted early, Nov 7 evening).

    PYTHONPATH=src ~/workspace/tools/composevenv/bin/python \
        scripts/chain_sig_dryrun.py

Proves the settlement primitive end to end, in the open:

1. DERIVE — the Solana address for uzemarkets-talent.testnet is
   derived client-side from the MPC testnet Ed25519 root key
   (ed25519:6vSEtQxrQj6txUMh33WC4ERyCWmNMRTdufDWAaDY3Un2, the value
   chainsig.js pins for v1.signer-prod.testnet) using near/mpc's
   tweak: sha3_256("near-mpc-recovery v0.1.0 epsilon derivation:"
   + predecessor + "," + path), read little-endian, reduced mod L;
   child = root + tweak*B on Edwards25519.
2. CROSS-CHECK — the contract's own derived_public_key view
   (domain_id 1) must return the identical key. Two independent
   routes agreeing is the verification; neither is taken on faith.
3. SIGN — a Solana devnet transfer message (derived address -> the
   recon account's derived address, 1 lamport) is signed by the MPC
   via py-near: v1.signer-prod.testnet `sign` with
   {request: {payload_v2: {Eddsa: <message bytes hex>}, path: "",
   domain_id: 1}}, 1 yoctoNEAR attached, per chainsig.js.
4. VERIFY — the returned 64-byte signature must verify under the
   derived public key over the exact message bytes (PyNaCl). A
   signature that verifies IS the proof the derived account is
   spendable by the NEAR identity. Broadcasting is Day 3.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import near_client  # noqa: E402  (credential loader + proxied provider)

PREDECESSOR = "uzemarkets-talent.testnet"
PATH = ""
SIGNER_CONTRACT = "v1.signer-prod.testnet"
ROOT_ED25519 = "ed25519:6vSEtQxrQj6txUMh33WC4ERyCWmNMRTdufDWAaDY3Un2"
SOLANA_DEVNET = "https://api.devnet.solana.com"

# --- Edwards25519 point arithmetic (RFC 8032 reference formulas) ---
_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _Q - 2, _Q) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)


def _decode_point(data: bytes) -> tuple[int, int]:
    bits = int.from_bytes(data, "little")
    x_sign = (bits >> 255) & 1
    y = bits & ((1 << 255) - 1)
    x2 = (y * y - 1) * pow(_D * y * y + 1, _Q - 2, _Q) % _Q
    x = pow(x2, (_Q + 3) // 8, _Q)
    if (x * x - x2) % _Q != 0:
        x = x * _I % _Q
    if (x * x - x2) % _Q != 0:
        raise ValueError("point decoding failed")
    if (x & 1) != x_sign:
        x = _Q - x
    return x, y


def _encode_point(x: int, y: int) -> bytes:
    bits = y | ((x & 1) << 255)
    return bits.to_bytes(32, "little")


def _point_add(p: tuple[int, int], q: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = p
    x2, y2 = q
    t = _D * x1 * x2 * y1 * y2 % _Q
    x3 = (x1 * y2 + x2 * y1) * pow(1 + t, _Q - 2, _Q) % _Q
    y3 = (y1 * y2 + x1 * x2) * pow(1 - t, _Q - 2, _Q) % _Q
    return x3, y3


def _point_mul(p: tuple[int, int], e: int) -> tuple[int, int]:
    result = (0, 1)
    addend = p
    while e:
        if e & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        e >>= 1
    return result


_BASE_Y = 4 * pow(5, _Q - 2, _Q) % _Q
_BASE_X = _decode_point(_encode_point(0, _BASE_Y))[0]
if (_BASE_X & 1) != 0:
    _BASE_X = _Q - _BASE_X
BASE_POINT = (_BASE_X, _BASE_Y)


def derive_solana_address(predecessor: str, path: str) -> tuple[str, bytes]:
    import base58

    root_bytes = base58.b58decode(ROOT_ED25519.split(":", 1)[1])
    root_point = _decode_point(root_bytes)
    tweak_hex = hashlib.sha3_256(
        f"near-mpc-recovery v0.1.0 epsilon derivation:{predecessor},{path}".encode()
    ).hexdigest()
    scalar = int.from_bytes(bytes.fromhex(tweak_hex), "little") % _L
    child = _point_add(root_point, _point_mul(BASE_POINT, scalar))
    child_bytes = _encode_point(*child)
    return base58.b58encode(child_bytes).decode(), child_bytes


async def _amain() -> int:
    from py_near.account import Account

    address, derived_bytes = derive_solana_address(PREDECESSOR, PATH)
    print(f"1. derived Solana address (client-side): {address}")

    account = Account(
        PREDECESSOR,
        near_client._load_private_key(PREDECESSOR),
        rpc_addr=near_client.RPC_ADDR,
    )
    account._provider = near_client._ProxiedProvider.build(near_client.RPC_ADDR)
    await account.startup()

    view = await account.view_function(
        SIGNER_CONTRACT,
        "derived_public_key",
        {"path": PATH, "predecessor": PREDECESSOR, "domain_id": 1},
    )
    contract_key = view.result
    print(f"2. contract derived_public_key view:    {contract_key}")
    assert contract_key == f"ed25519:{__import__('base58').b58encode(derived_bytes).decode()}", (
        "client derivation disagrees with the contract's own view"
    )
    print("   MATCH — derivation verified by the contract itself")

    # Build a Solana devnet transfer message: derived -> recon derived.
    from solders.hash import Hash
    from solders.message import Message
    from solders.pubkey import Pubkey
    from solders.system_program import TransferParams, transfer

    recon_address, _ = derive_solana_address("recon.uzemarkets-talent.testnet", PATH)
    # curl via subprocess: it is this VM's proven egress path (httpx's
    # env parsing chokes on the IPv6 no_proxy entries; urllib's proxy
    # CONNECT is refused). One small JSON-RPC post.
    import subprocess

    out = subprocess.run(
        [
            "curl", "-s", SOLANA_DEVNET,
            "-H", "Content-Type: application/json",
            "-d", '{"jsonrpc":"2.0","id":1,"method":"getLatestBlockhash"}',
        ],
        capture_output=True, text=True, timeout=30, check=True,
    )
    blockhash = json.loads(out.stdout)["result"]["value"]["blockhash"]
    ix = transfer(
        TransferParams(
            from_pubkey=Pubkey.from_string(address),
            to_pubkey=Pubkey.from_string(recon_address),
            lamports=1,
        )
    )
    message = Message.new_with_blockhash(
        [ix], Pubkey.from_string(address), Hash.from_string(blockhash)
    )
    message_bytes = bytes(message)
    print(f"3. solana devnet message built: {len(message_bytes)} bytes "
          f"({address} -> {recon_address}, 1 lamport)")

    result = await account.function_call(
        SIGNER_CONTRACT,
        "sign",
        {
            "request": {
                "payload_v2": {"Eddsa": message_bytes.hex()},
                "path": PATH,
                "domain_id": 1,
            }
        },
        gas=300_000_000_000_000,
        amount=1,
    )
    value = None
    if isinstance(result.status, dict) and result.status.get("SuccessValue"):
        value = json.loads(base64.b64decode(result.status["SuccessValue"]))
    print(f"4. MPC sign answered (tx {result.transaction.hash}): "
          f"{json.dumps(value)[:200]}")

    sig_bytes = _extract_signature(value)
    print(f"   signature: {len(sig_bytes)} bytes")

    from nacl.signing import VerifyKey

    VerifyKey(derived_bytes).verify(message_bytes, sig_bytes)
    print("5. VERIFIED — the MPC signature verifies under the derived key")
    print()
    print(f"CHAIN SIGNATURES: GO — {PREDECESSOR} controls Solana address "
          f"{address} via {SIGNER_CONTRACT}")
    return 0


def _extract_signature(value) -> bytes:
    """The EdDSA MPC response shapes seen in the wild:
    {"signature": [64 ints]} | {"signature": "<hex>"} | [64 ints]."""
    if isinstance(value, dict):
        value = value.get("signature", value)
    if isinstance(value, list):
        return bytes(value)
    if isinstance(value, str):
        return bytes.fromhex(value)
    raise ValueError(f"unrecognized signature shape: {type(value)} {value!r:.200}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_amain()))
