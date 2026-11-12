import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import SwaggerDocs from "@/components/swagger-docs";
import { CONTENT, isLocale, type Locale } from "@/lib/devpartner";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  return { title: CONTENT[locale].docs.title };
}

export default async function DevPartnerDocsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const c = CONTENT[locale as Locale];

  return (
    <main className="dp">
      <p>
        <Link href={`/devpartner/${locale}`}>{c.docs.back}</Link>
      </p>
      <h1>{c.docs.title}</h1>
      <p>{c.docs.body}</p>
      <SwaggerDocs />
    </main>
  );
}
