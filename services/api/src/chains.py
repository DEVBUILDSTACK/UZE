"""Chain configuration for UZE multi-chain ticket commerce.

Solana: primary chain — USDC x402 micro-transactions, Phantom WaaS.
LightLink: EVM L2 for NFT tickets — gasless enterprise mode.
Bridging between them: Stargate (LayerZero).
"""
CHAINS = {
    "solana": {
        "name": "Solana",
        "kind": "svm",
        "usdc_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # mainnet
        "role": "primary payments + x402",
    },
    "lightlink": {
        "name": "LightLink",
        "kind": "evm",
        "chain_id": 1890,  # mainnet
        "rpc": "https://replicator.pegasus.lightlink.io/rpc/v1",
        "role": "gasless NFT tickets (enterprise mode)",
        "bridge": "stargate/layerzero",
        "bridge_assets": ["ETH", "USDC", "USDT", "LL"],
    },
}

# Canonical NFT ticket standard per chain (team confirms contract addresses).
NFT_STANDARDS = {
    "solana": "metaplex-core",
    "lightlink": "erc721",
}
