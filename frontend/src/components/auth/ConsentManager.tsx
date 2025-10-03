/**
 * 同意管理コンポーネント
 *
 * ユーザーの同意状況管理とCookie同意機能を提供
 * GDPR および個人情報保護法に準拠した同意管理
 */

import React, { useState, useEffect } from "react";
import Link from "next/link";

// 同意種別の定義
export type ConsentType = "privacy_policy" | "terms_of_service" | "cookie_policy" | "marketing";

// 同意状況の型定義
export interface ConsentStatus {
  consented: boolean;
  version: string;
  date: string | null;
}

// 同意管理の型定義
export interface ConsentData {
  privacy_policy?: ConsentStatus;
  terms_of_service?: ConsentStatus;
  cookie_policy?: ConsentStatus;
  marketing?: ConsentStatus;
}

interface ConsentManagerProps {
  /** 初期同意データ */
  initialConsents?: ConsentData;
  /** 同意変更時のコールバック */
  onConsentChange?: (consentType: ConsentType, consented: boolean) => void;
  /** 必須同意項目 */
  requiredConsents?: ConsentType[];
  /** 表示モード */
  mode?: "registration" | "settings" | "banner";
  /** クラス名 */
  className?: string;
}

const ConsentManager: React.FC<ConsentManagerProps> = ({
  initialConsents = {},
  onConsentChange,
  requiredConsents = ["privacy_policy", "terms_of_service"],
  mode = "registration",
  className = "",
}) => {
  const [consents, setConsents] = useState<ConsentData>(initialConsents);
  const [showCookieBanner, setShowCookieBanner] = useState(false);

  // Cookie同意の確認
  useEffect(() => {
    if (mode === "banner") {
      const cookieConsent = localStorage.getItem("cookie_consent");
      if (!cookieConsent) {
        setShowCookieBanner(true);
      }
    }
  }, [mode]);

  // 同意状況の更新
  const handleConsentChange = (consentType: ConsentType, consented: boolean) => {
    const newConsents = {
      ...consents,
      [consentType]: {
        consented,
        version: "1.0",
        date: new Date().toISOString(),
      },
    };

    setConsents(newConsents);

    // Cookie同意の場合はローカルストレージに保存
    if (consentType === "cookie_policy") {
      localStorage.setItem("cookie_consent", consented ? "accepted" : "rejected");
      if (consented) {
        setShowCookieBanner(false);
      }
    }

    // コールバック実行
    if (onConsentChange) {
      onConsentChange(consentType, consented);
    }
  };

  // 全ての必須同意が完了しているかチェック
  const areRequiredConsentsGiven = () => {
    return requiredConsents.every((consentType) => consents[consentType]?.consented === true);
  };

  // Cookie バナーの表示
  if (mode === "banner" && showCookieBanner) {
    return (
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-4 z-50">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
          <div className="flex-1">
            <p className="text-sm">
              このサイトでは、サービス向上のためにCookieを使用しています。
              <Link href="/privacy" className="text-blue-300 hover:text-blue-200 ml-1">
                プライバシーポリシー
              </Link>
              をご確認ください。
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => handleConsentChange("cookie_policy", false)}
              className="px-4 py-2 text-sm border border-gray-600 rounded hover:bg-gray-800 transition"
            >
              拒否
            </button>
            <button onClick={() => handleConsentChange("cookie_policy", true)} className="px-4 py-2 text-sm bg-blue-600 rounded hover:bg-blue-700 transition">
              同意する
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 登録時の同意チェックボックス
  if (mode === "registration") {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="space-y-3">
          {/* プライバシーポリシー同意 */}
          <div className="flex items-start">
            <input
              id="consent-privacy"
              type="checkbox"
              checked={consents.privacy_policy?.consented || false}
              onChange={(e) => handleConsentChange("privacy_policy", e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
              required={requiredConsents.includes("privacy_policy")}
            />
            <label htmlFor="consent-privacy" className="ml-3 text-sm text-gray-700">
              <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
                プライバシーポリシー
              </Link>
              に同意します
              {requiredConsents.includes("privacy_policy") && <span className="text-red-500 ml-1">*</span>}
            </label>
          </div>

          {/* 利用規約同意 */}
          <div className="flex items-start">
            <input
              id="consent-terms"
              type="checkbox"
              checked={consents.terms_of_service?.consented || false}
              onChange={(e) => handleConsentChange("terms_of_service", e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
              required={requiredConsents.includes("terms_of_service")}
            />
            <label htmlFor="consent-terms" className="ml-3 text-sm text-gray-700">
              <Link href="/terms" className="text-blue-600 hover:text-blue-500">
                利用規約
              </Link>
              に同意します
              {requiredConsents.includes("terms_of_service") && <span className="text-red-500 ml-1">*</span>}
            </label>
          </div>

          {/* マーケティング同意（任意） */}
          <div className="flex items-start">
            <input
              id="consent-marketing"
              type="checkbox"
              checked={consents.marketing?.consented || false}
              onChange={(e) => handleConsentChange("marketing", e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
            />
            <label htmlFor="consent-marketing" className="ml-3 text-sm text-gray-700">
              マーケティング情報の受信に同意します（任意）
            </label>
          </div>
        </div>

        {/* 必須同意の警告 */}
        {!areRequiredConsentsGiven() && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-sm text-yellow-800">
              <span className="text-red-500">*</span>
              必須項目への同意が必要です
            </p>
          </div>
        )}
      </div>
    );
  }

  // 設定画面での同意管理
  if (mode === "settings") {
    return (
      <div className={`bg-white shadow rounded-lg p-6 ${className}`}>
        <h3 className="text-lg font-medium text-gray-900 mb-6">同意設定</h3>

        <div className="space-y-6">
          {/* プライバシーポリシー */}
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">プライバシーポリシー</h4>
              <p className="text-sm text-gray-500">個人情報の取扱いに関する方針への同意</p>
              {consents.privacy_policy?.date && (
                <p className="text-xs text-gray-400 mt-1">同意日時: {new Date(consents.privacy_policy.date).toLocaleString("ja-JP")}</p>
              )}
            </div>
            <div className="ml-4">
              <span
                className={`px-2 py-1 text-xs rounded-full ${consents.privacy_policy?.consented ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}
              >
                {consents.privacy_policy?.consented ? "同意済み" : "未同意"}
              </span>
            </div>
          </div>

          {/* 利用規約 */}
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">利用規約</h4>
              <p className="text-sm text-gray-500">サービス利用に関する規約への同意</p>
              {consents.terms_of_service?.date && (
                <p className="text-xs text-gray-400 mt-1">同意日時: {new Date(consents.terms_of_service.date).toLocaleString("ja-JP")}</p>
              )}
            </div>
            <div className="ml-4">
              <span
                className={`px-2 py-1 text-xs rounded-full ${consents.terms_of_service?.consented ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}
              >
                {consents.terms_of_service?.consented ? "同意済み" : "未同意"}
              </span>
            </div>
          </div>

          {/* Cookie ポリシー */}
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">Cookie の使用</h4>
              <p className="text-sm text-gray-500">Cookie を使用したサービス向上への同意</p>
              {consents.cookie_policy?.date && (
                <p className="text-xs text-gray-400 mt-1">同意日時: {new Date(consents.cookie_policy.date).toLocaleString("ja-JP")}</p>
              )}
            </div>
            <div className="ml-4 flex items-center space-x-2">
              <button
                onClick={() => handleConsentChange("cookie_policy", !consents.cookie_policy?.consented)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  consents.cookie_policy?.consented ? "bg-blue-600" : "bg-gray-200"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    consents.cookie_policy?.consented ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>

          {/* マーケティング */}
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">マーケティング情報</h4>
              <p className="text-sm text-gray-500">製品情報やプロモーションの受信への同意</p>
              {consents.marketing?.date && <p className="text-xs text-gray-400 mt-1">同意日時: {new Date(consents.marketing.date).toLocaleString("ja-JP")}</p>}
            </div>
            <div className="ml-4 flex items-center space-x-2">
              <button
                onClick={() => handleConsentChange("marketing", !consents.marketing?.consented)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  consents.marketing?.consented ? "bg-blue-600" : "bg-gray-200"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    consents.marketing?.consented ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            同意の撤回はいつでも可能です。詳細は
            <Link href="/privacy" className="text-blue-600 hover:text-blue-500 ml-1">
              プライバシーポリシー
            </Link>
            をご確認ください。
          </p>
        </div>
      </div>
    );
  }

  return null;
};

export default ConsentManager;
