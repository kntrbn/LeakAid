"use client";

import { usePathname } from "next/navigation";
import { Header } from "./Header";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // ログインページではヘッダーなし・フルスクリーン
  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="mx-auto flex h-dvh max-w-lg flex-col">
      <Header />
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
