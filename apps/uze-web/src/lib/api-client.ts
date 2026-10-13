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

export const ApiGet = <T>(url: string, params?: object) =>
  api.get<T>(url, { params }).then((r) => r.data);
export const ApiPost = <T>(url: string, body?: object) =>
  api.post<T>(url, body).then((r) => r.data);
export const ApiPut = <T>(url: string, body?: object) =>
  api.put<T>(url, body).then((r) => r.data);
export const ApiDelete = <T>(url: string) =>
  api.delete<T>(url).then((r) => r.data);
