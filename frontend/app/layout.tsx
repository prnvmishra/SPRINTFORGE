import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";

import { Providers } from "@/components/providers";

import "./globals.css";

/** UI text: neutral, precise, excellent at small sizes. */
const sans = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

/** Editorial display voice for marketing headlines and large numbers. */
const display = Space_Grotesk({
  subsets: ["latin"],
  display: "swap",
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

/** Everything the machine says: code, ids, metrics, system labels. */
const mono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "SprintForge.AI — Don't learn what you already know",
  description:
    "An AI-powered personalised learning path recommender. SprintForge verifies what you know, watches how you build, and continuously adapts what you learn next.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`dark ${sans.variable} ${display.variable} ${mono.variable}`}
    >
      <body className="min-h-screen bg-canvas font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
