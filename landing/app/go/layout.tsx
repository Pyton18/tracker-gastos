import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Spend Tracker — Open app",
  robots: { index: false, follow: false },
};

export default function GoLayout({ children }: { children: React.ReactNode }) {
  return children;
}
