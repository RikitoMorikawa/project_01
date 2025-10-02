import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";

export interface NavigationItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
  requiresAuth?: boolean;
}

export interface NavigationProps {
  items: NavigationItem[];
  isAuthenticated?: boolean;
  orientation?: "horizontal" | "vertical";
  className?: string;
  showMobileMenu?: boolean;
  onMobileMenuToggle?: () => void;
}

const Navigation: React.FC<NavigationProps> = ({
  items,
  isAuthenticated = false,
  orientation = "horizontal",
  className = "",
  showMobileMenu = false,
  onMobileMenuToggle,
}) => {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // 認証が必要なアイテムをフィルタリング
  const visibleItems = items.filter((item) => !item.requiresAuth || isAuthenticated);

  const isActiveRoute = (href: string) => {
    return router.pathname === href;
  };

  const handleMobileMenuToggle = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
    onMobileMenuToggle?.();
  };

  const linkClasses = (href: string) => {
    const baseClasses = "flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors";
    const activeClasses = "bg-blue-100 text-blue-700";
    const inactiveClasses = "text-gray-600 hover:text-gray-900 hover:bg-gray-50";

    return `${baseClasses} ${isActiveRoute(href) ? activeClasses : inactiveClasses}`;
  };

  if (orientation === "vertical") {
    return (
      <nav className={`space-y-1 ${className}`}>
        {visibleItems.map((item) => (
          <Link key={item.href} href={item.href} className={linkClasses(item.href)}>
            {item.icon && <span className="w-5 h-5">{item.icon}</span>}
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    );
  }

  return (
    <>
      {/* デスクトップナビゲーション */}
      <nav className={`hidden md:flex items-center space-x-4 ${className}`}>
        {visibleItems.map((item) => (
          <Link key={item.href} href={item.href} className={linkClasses(item.href)}>
            {item.icon && <span className="w-5 h-5">{item.icon}</span>}
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* モバイルメニューボタン */}
      <div className="md:hidden">
        <button
          onClick={handleMobileMenuToggle}
          className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
          aria-expanded="false"
        >
          <span className="sr-only">メニューを開く</span>
          {isMobileMenuOpen ? (
            <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* モバイルナビゲーション */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 bg-white shadow-lg border-t border-gray-200 z-50">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {visibleItems.map((item) => (
              <Link key={item.href} href={item.href} className={linkClasses(item.href)} onClick={() => setIsMobileMenuOpen(false)}>
                {item.icon && <span className="w-5 h-5">{item.icon}</span>}
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </>
  );
};

export default Navigation;
