/** Standalone output only for container/CI builds (Fundio pattern).
 *  Local `next build` stays normal; Docker/CI sets DOCKER=true. */
const isContainer = process.env.DOCKER === "true" || process.env.CI === "true";

const nextConfig = {
  ...(isContainer ? { output: "standalone" } : {}),
  images: { unoptimized: true },
};

export default nextConfig;
