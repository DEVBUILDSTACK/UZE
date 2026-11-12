import { createConfig, http } from "wagmi";
import { base, mainnet } from "wagmi/chains";

/** Wagmi config (treasury port, 2026-11-11 — owner's override).
 *  Minimal surface: Base (Coinbase on-ramp destination) and
 *  Ethereum mainnet, injected-wallet connectors (wagmi default),
 *  SSR-safe. Cross-chain movement itself runs through Wormhole
 *  Connect (Move tab), which manages its own wallet plumbing. */
export const wagmiConfig = createConfig({
  chains: [base, mainnet],
  transports: {
    [base.id]: http(),
    [mainnet.id]: http(),
  },
  ssr: true,
});
