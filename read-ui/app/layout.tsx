import type { Metadata } from "next";
import { Chivo, Noto_Sans } from "next/font/google";
import "@/styles/globals.scss";

// Same families and weights the WorldFish site loads in app/layout.js — Noto Sans for
// headings, Chivo for body — exposed as the CSS vars the tokens reference (--noto / --chivo).
const chivo = Chivo({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--chivo",
  display: "swap",
});

const noto = Noto_Sans({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--noto",
  display: "swap",
});

export const metadata: Metadata = {
  title: "WDB — WorldFish Digital Brain",
  description:
    "Ask the shared knowledge base a question and see a grounded answer with its sources and the graph associations around it. Read-only.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${chivo.variable} ${noto.variable}`}>
      <body>{children}</body>
    </html>
  );
}
