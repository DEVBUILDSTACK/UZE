"""NFTs router — onchain ticket records (multi-chain).

Offchain ticket state lives in /tickets; this router records the onchain
mint (chain, contract, token id). Minting itself is team build work
(Solana program / LightLink ERC-721); the API tracks the linkage.
"""
from fastapi import APIRouter, Depends

from src.auth import require_auth
from src.chains import CHAINS, NFT_STANDARDS
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/nfts", tags=["nfts"])


@router.get("/chains", response_model=APIResponse[dict])
async def supported_chains():
    return ok(
        {
            name: {"role": c["role"], "kind": c["kind"],
                   "nft_standard": NFT_STANDARDS[name]}
            for name, c in CHAINS.items()
        }
    )


@router.post("/mint-record", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def mint_record(payload: dict):
    # payload: {ticketId, chain, contractAddress, tokenId, txHash}
    # Team build: verify the mint onchain before recording.
    return ok(payload, message="Mint recorded")
