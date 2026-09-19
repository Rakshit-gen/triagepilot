import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "triagepilot",
  description: "Agentic support ticket triage with a human-approved final step.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
