import React from "react";
import Link from "next/link";
import { Button } from "../ui";
import Navigation, { NavigationItem } from "./Navigation";

export interface HeaderProps {
  title?: string;
  showAuth?: boolean;
  isAuthenticated?: boolean;
  user?: {
    username: string;
    email: string;
  } | null;
  onLogin?: () => void;
  onLogout?: () => void;
  navigationItems?: NavigationItem[];
  showNavigation?: boolean;
}

const Header: React.FC<HeaderProps> = ({
  title = "CSR Lambda API",
  showAuth = true,
  isAuthenticated = false,
  user = null,
  onLogin,
  onLogout,
  navigationItems = [],
  showNavigation = true,
}) => {
  // デフォルトのナビゲーションアイテム
  const defaultNavigationItems: NavigationItem[] = [
    { label: "ホーム", href: "/" },
    { label: "ダッシュボード", href: "/dashboard", requiresAuth: true },
    { label: "プロフィール", href: "/profile", requiresAuth: true },
    { label: "サービスについて", href: "/about" },
  ];

  const navItems = navigationItems.length > 0 ? navigationItems : defaultNavigationItems;
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container">
        <div className="flex items-center justify-between h-16">
          {/* ロゴ・タイトル */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-gray-900">{title}</span>
            </Link>
          </div>

          {/* ナビゲーション */}
          {showNavigation && <Navigation items={navItems} isAuthenticated={isAuthenticated} orientation="horizontal" />}

          {/* 認証ボタン */}
          {showAuth && (
            <div className="flex items-center space-x-4">
              {isAuthenticated && user ? (
                <div className="flex items-center space-x-3">
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-gray-900">{user.username}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-gray-700">{user.username.charAt(0).toUpperCase()}</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={onLogout}>
                    ログアウト
                  </Button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm" onClick={onLogin}>
                    ログイン
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      /* 登録処理 */
                    }}
                  >
                    新規登録
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
