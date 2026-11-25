import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitHub Elite | A stronger gym starts behind the scenes",
  description: "One connected workspace for gym members, memberships, attendance, coaching and everyday operations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
