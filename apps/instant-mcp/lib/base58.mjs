// Base58 (Bitcoin alphabet) encode/decode — a Solana wallet address is
// the base58 encoding of a 32-byte ed25519 public key. Zero-dependency.
const ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const INDEX = new Map([...ALPHABET].map((c, i) => [c, BigInt(i)]));

export function base58Encode(bytes) {
  let zeros = 0;
  while (zeros < bytes.length && bytes[zeros] === 0) zeros++;
  let n = 0n;
  for (const b of bytes) n = n * 256n + BigInt(b);
  let out = "";
  while (n > 0n) { out = ALPHABET[Number(n % 58n)] + out; n /= 58n; }
  return "1".repeat(zeros) + out;
}

export function base58Decode(str) {
  if (typeof str !== "string" || str.length === 0) throw new Error("invalid base58: empty");
  let zeros = 0;
  while (zeros < str.length && str[zeros] === "1") zeros++;
  let n = 0n;
  for (const c of str) {
    if (!INDEX.has(c)) throw new Error(`invalid base58 character: ${c}`);
    n = n * 58n + INDEX.get(c);
  }
  const bytes = [];
  while (n > 0n) { bytes.unshift(Number(n % 256n)); n /= 256n; }
  return Buffer.concat([Buffer.alloc(zeros), Buffer.from(bytes)]);
}
