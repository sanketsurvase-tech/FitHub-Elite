import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitHub Elite | Gym management",
  description: "A connected workspace for modern gym operations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
