"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./AuthProvider";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user && pathname !== "/login") {
      router.replace("/login");
    }
  }, [user, loading, pathname, router]);

  if (loading) {
    return (
      <div className="flex h-dvh items-center justify-center text-sm text-gray-400">
        読み込み中...
      </div>
    );
  }

  // ログインページは認証不要
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // 未ログインならリダイレクト中（何も表示しない）
  if (!user) return null;

  return <>{children}</>;
}
