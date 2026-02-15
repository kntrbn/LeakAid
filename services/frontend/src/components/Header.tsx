"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "./AuthProvider";

const NAV = [
  { href: "/", label: "チャット" },
  { href: "/status", label: "ステータス" },
] as const;

function getInitials(email: string | undefined): string {
  if (!email) return "?";
  return email[0].toUpperCase();
}

export function Header() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // メニュー外クリックで閉じる
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [menuOpen]);

  const avatarUrl = user?.user_metadata?.avatar_url as string | undefined;
  const displayName =
    (user?.user_metadata?.full_name as string | undefined) ??
    user?.email ??
    "";

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="flex items-center">
        {/* ナビゲーション */}
        <nav className="flex flex-1">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`flex-1 py-3 text-center text-sm font-medium transition-colors ${
                pathname === href
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* ユーザーアバター */}
        <div className="relative px-3" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-blue-600 text-sm font-medium text-white transition-opacity hover:opacity-80"
          >
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              getInitials(user?.email)
            )}
          </button>

          {/* ドロップダウンメニュー */}
          {menuOpen && (
            <div className="absolute right-0 top-full z-50 mt-1 w-64 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
              {/* ユーザー情報 */}
              <div className="border-b border-gray-100 px-4 py-3">
                <p className="truncate text-sm font-medium text-gray-900">
                  {displayName}
                </p>
                {displayName !== user?.email && (
                  <p className="truncate text-xs text-gray-500">
                    {user?.email}
                  </p>
                )}
              </div>

              {/* メニュー項目 */}
              <Link
                href="/billing"
                onClick={() => setMenuOpen(false)}
                className="flex w-full items-center px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50"
              >
                課金管理
              </Link>

              <div className="border-t border-gray-100">
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    signOut();
                  }}
                  className="flex w-full items-center px-4 py-2.5 text-left text-sm text-red-600 hover:bg-gray-50"
                >
                  ログアウト
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
