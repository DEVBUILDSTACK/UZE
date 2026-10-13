/** Typed API client for the UZE monolithic backend.
 *  Pattern lifted from Fundio's src/lib/api-helper.ts:
 *  one axios instance, baseURL from env, Bearer auth, 401 redirect. */
import axios from "axios";
import { ENV } from "./env";

export const api = axios.create({
  baseURL: ENV.apiBaseUrl,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

/** Attach a Bearer token (Privy/JWT) to subsequent requests. */
export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401 && typeof window !== "undefined") {
      setAuthToken(null);
      window.location.href = "/auth";
    }
    return Promise.reject(err);
  }
);

/** Backend envelope — mirrors the FastAPI APIResponse[T] contract:
 *  { status_code, message, data, metadata }. Helpers unwrap `data`. */
interface ApiEnvelope<T> {
  status_code: number;
  message: string;
  data: T;
  metadata?: Record<string, unknown>;
}

export const ApiGet = <T>(url: string, params?: object) =>
  api.get<ApiEnvelope<T>>(url, { params }).then((r) => r.data.data);
export const ApiPost = <T>(url: string, body?: object) =>
  api.post<ApiEnvelope<T>>(url, body).then((r) => r.data.data);
export const ApiPut = <T>(url: string, body?: object) =>
  api.put<ApiEnvelope<T>>(url, body).then((r) => r.data.data);
export const ApiDelete = <T>(url: string) =>
  api.delete<ApiEnvelope<T>>(url).then((r) => r.data.data);

/** Operator login — POST /auth/login -> { access_token, token_type }. */
export async function login(email_address: string, password: string) {
  const { access_token } = await ApiPost<{ access_token: string; token_type: string }>(
    "/auth/login",
    { email_address, password }
  );
  setAuthToken(access_token);
  return access_token;
}
