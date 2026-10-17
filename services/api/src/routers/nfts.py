"""NFTs router — onchain ticket records (multi-chain).

Offchain ticket state lives in /tickets; this router records the onchain
mint (chain, contract, token id). Minting itself is team build work
(Solana program / LightLink ERC-721); the API tracks the linkage.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.auth import require_auth
from src.chains import CHAINS, NFT_STANDARDS
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/nfts", tags=["nfts"])


class MintRecordIn(BaseModel):
    ticketId: str
    chain: str = Field(max_length=40)
    contractAddress: str = Field(max_length=100)
    tokenId: str = Field(max_length=100)
    txHash: str = Field(max_length=120)


@router.get("/chains", response_model=APIResponse[dict])
async def supported_chains():
    return ok(
        {
            name: {"role": c["role"], "kind": c["kind"],
                   "nft_standard": NFT_STANDARDS[name]}
            for name, c in CHAINS.items()
        }
    )


@router.post("/mint-record", response_model=APIResponse[dict])
async def mint_record(
    body: MintRecordIn, user_id: str = Depends(require_auth)
):
    # Team build: verify the mint onchain before recording.
    return ok(body.model_dump(), message="Mint recorded")
