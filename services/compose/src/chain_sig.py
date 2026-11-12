"""Chain Signatures primitives for the composition layer (Sprint 1.5).

The derivation and signing proven in scripts/chain_sig_dryrun.py,
productionized:

- derive_address(predecessor, path) — the Solana address a NEAR
  account controls through the MPC signer, computed client-side from
  the testnet Ed25519 root key using near/mpc's tweak (sha3-256 of
  "near-mpc-recovery v0.1.0 epsilon derivation:<predecessor>,<path>",
  little-endian, reduced mod L; child = root + tweak*B on
  Edwards25519). Verified on 2026-11-07 against the contract's own
  derived_public_key view — the two routes agree exactly.
- mpc_sign(predecessor, payload) — asks v1.signer-prod.testnet to
  sign payload bytes with the predecessor's derived Ed25519 key
  (payload_v2 Eddsa, domain_id 1, 1 yoctoNEAR, per chainsig.js) and
  returns the 64-byte signature. The call is made BY the predecessor
  account itself — the MPC derives from the caller, so no other
  account can request this signature.

Sync wrappers throughout: the compose runtime is sync FastAPI defs,
so each call runs its own event loop, as near_client.py does.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json

import near_client

SIGNER_CONTRACT = "v1.signer-prod.testnet"
ROOT_ED25519 = "ed25519:6vSEtQxrQj6txUMh33WC4ERyCWmNMRTdufDWAaDY3Un2"

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
if _BASE_X & 1:
    _BASE_X = _Q - _BASE_X
BASE_POINT = (_BASE_X, _BASE_Y)


def derive_address(predecessor: str, path: str = "") -> tuple[str, bytes]:
    """(base58 Solana address, derived public key bytes) for a NEAR
    account + derivation path, via the MPC Ed25519 root."""
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


async def _mpc_sign(predecessor: str, payload: bytes, path: str) -> bytes:
    from py_near.account import Account

    account = Account(
        predecessor,
        near_client._load_private_key(predecessor),
        rpc_addr=near_client.RPC_ADDR,
    )
    account._provider = near_client._ProxiedProvider.build(near_client.RPC_ADDR)
    await account.startup()
    result = await account.function_call(
        SIGNER_CONTRACT,
        "sign",
        {
            "request": {
                "payload_v2": {"Eddsa": payload.hex()},
                "path": path,
                "domain_id": 1,
            }
        },
        gas=300_000_000_000_000,
        amount=1,
    )
    if not (isinstance(result.status, dict) and result.status.get("SuccessValue")):
        raise RuntimeError(f"MPC sign returned no signature: {result.status}")
    value = json.loads(base64.b64decode(result.status["SuccessValue"]))
    signature = value.get("signature") if isinstance(value, dict) else value
    if isinstance(signature, list):
        return bytes(signature)
    if isinstance(signature, str):
        return bytes.fromhex(signature)
    raise RuntimeError(f"unrecognized MPC signature shape: {type(signature)}")


def mpc_sign(predecessor: str, payload: bytes, path: str = "") -> bytes:
    """The predecessor's 64-byte Ed25519 signature over payload,
    produced by the NEAR MPC network."""
    return asyncio.run(_mpc_sign(predecessor, payload, path))
