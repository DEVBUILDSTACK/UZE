/** Centralized env accessor (Fundio src/lib/env.ts pattern).
 *  Fail fast at build time instead of non-null asserts scattered in code. */
function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Missing required env var ${name}. See .env.example at the repo root.`
    );
  }
  return value;
}

export const ENV = {
  baseUrl: process.env.NEXT_PUBLIC_BASE_URL ?? "https://uzemarkets.com",
  // Required in every deployed env; falls back to local API for `pnpm dev`.
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
} as const;

// Call once in a route/layout that must not render without backend config.
export function assertEnv() {
  if (process.env.NODE_ENV === "production") {
    required("NEXT_PUBLIC_API_BASE_URL");
  }
}
