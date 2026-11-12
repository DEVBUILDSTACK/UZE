import type { MetadataRoute } from "next";
import { ENV } from "@/lib/env";

export default function robots(): MetadataRoute.Robots {
  const base = ENV.baseUrl.replace(/\/$/, "");
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${base}/sitemap.xml`,
  };
}
