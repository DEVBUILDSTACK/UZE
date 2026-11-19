import type { ReactNode } from "react";
import C3Shell from "@/components/c3-shell";

export const metadata = {
  title: "C3 Admin Hub — UZEmarkets",
  description:
    "The UZEmarkets Command & Control Console for business entity owner partners and their officers. Corporate email, one-time code.",
  robots: { index: false, follow: false },
};

export default function C3Layout({ children }: { children: ReactNode }) {
  return <C3Shell>{children}</C3Shell>;
}
