/** SocialFi onboarding API helpers — email OTP -> 20-second profile.
 *  Talks to the UZE monolithic backend (see services/api/src/otp.py,
 *  services/api/src/routers/profiles.py). */
import { ApiGet, ApiPost, setAuthToken } from "@/lib/api-client";

const TOKEN_KEY = "uze_token";

export function saveToken(token: string) {
  setAuthToken(token);
  if (typeof window !== "undefined") localStorage.setItem(TOKEN_KEY, token);
}

export function loadToken(): string | null {
  if (typeof window === "undefined") return null;
  const t = localStorage.getItem(TOKEN_KEY);
  if (t) setAuthToken(t);
  return t;
}

export async function requestOtp(email_address: string) {
  return ApiPost<{ sent: boolean }>("/auth/otp/request", { email_address });
}

export async function verifyOtp(email_address: string, code: string) {
  const { access_token } = await ApiPost<{
    access_token: string;
    token_type: string;
    new_user: boolean;
  }>("/auth/otp/verify", { email_address, code });
  saveToken(access_token);
  return access_token;
}

export async function checkHandle(handle: string) {
  return ApiGet<{ available: boolean; reason?: string }>(
    `/profiles/check/${encodeURIComponent(handle)}`
  );
}

export interface ProfileCreate {
  handle: string;
  bio?: string;
  avatarUrl?: string;
  interests?: string[];
  referredBy?: string;
}

export async function createProfile(body: ProfileCreate) {
  return ApiPost<{ handle: string; referralCode: string }>("/profiles", body);
}

export async function getProfile(handle: string) {
  return ApiGet<{
    handle: string;
    bio: string | null;
    avatarUrl: string | null;
    interests: string[];
    createdAt: string;
  }>(`/profiles/${encodeURIComponent(handle)}`);
}
