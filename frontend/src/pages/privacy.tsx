/**
 * プライバシーポリシーページ
 *
 * 個人情報保護方針とデータ処理に関する詳細情報を表示
 * GDPR および個人情報保護法に準拠した内容
 */

import React from "react";
import Head from "next/head";
import Link from "next/link";

const PrivacyPolicyPage: React.FC = () => {
  return (
    <>
      <Head>
        <title>プライバシーポリシー | CSR Lambda API システム</title>
        <meta name="description" content="CSR Lambda API システムのプライバシーポリシー・個人情報保護方針" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* ヘッダー */}
          <div className="bg-white shadow rounded-lg p-8 mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">プライバシーポリシー</h1>
            <p className="text-gray-600 mb-4">最終更新日: 2024年1月1日 | バージョン: 1.0</p>
            <p className="text-gray-700">
              CSR Lambda API システム（以下「本サービス」）は、ユーザーの個人情報保護を重要視し、 個人情報保護法および
              GDPR（EU一般データ保護規則）に準拠して個人情報を取り扱います。
            </p>
          </div>

          {/* 目次 */}
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">目次</h2>
            <nav className="space-y-2">
              <a href="#section1" className="block text-blue-600 hover:text-blue-500">
                1. 収集する個人情報
              </a>
              <a href="#section2" className="block text-blue-600 hover:text-blue-500">
                2. 個人情報の利用目的
              </a>
              <a href="#section3" className="block text-blue-600 hover:text-blue-500">
                3. 個人情報の第三者提供
              </a>
              <a href="#section4" className="block text-blue-600 hover:text-blue-500">
                4. 個人情報の保管・セキュリティ
              </a>
              <a href="#section5" className="block text-blue-600 hover:text-blue-500">
                5. ユーザーの権利
              </a>
              <a href="#section6" className="block text-blue-600 hover:text-blue-500">
                6. Cookie の使用
              </a>
              <a href="#section7" className="block text-blue-600 hover:text-blue-500">
                7. データ保持期間
              </a>
              <a href="#section8" className="block text-blue-600 hover:text-blue-500">
                8. お問い合わせ
              </a>
            </nav>
          </div>

          {/* セクション1: 収集する個人情報 */}
          <section id="section1" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">1. 収集する個人情報</h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">1.1 アカウント登録時に収集する情報</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-2">
                  <li>メールアドレス（ログイン認証用）</li>
                  <li>ユーザー名（表示用）</li>
                  <li>パスワード（暗号化して保存）</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">1.2 プロファイル情報（任意）</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-2">
                  <li>氏名（姓・名）</li>
                  <li>プロフィール画像</li>
                  <li>自己紹介文</li>
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">1.3 自動的に収集される情報</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-2">
                  <li>IPアドレス</li>
                  <li>ブラウザ情報（User-Agent）</li>
                  <li>アクセス日時</li>
                  <li>操作ログ（セキュリティ目的）</li>
                </ul>
              </div>
            </div>
          </section>

          {/* セクション2: 利用目的 */}
          <section id="section2" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">2. 個人情報の利用目的</h2>

            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-medium text-gray-900">サービス提供</h3>
                <p className="text-gray-700">ユーザーアカウントの管理、認証、サービス機能の提供</p>
              </div>

              <div className="border-l-4 border-green-500 pl-4">
                <h3 className="font-medium text-gray-900">セキュリティ確保</h3>
                <p className="text-gray-700">不正アクセスの検知・防止、システムセキュリティの維持</p>
              </div>

              <div className="border-l-4 border-yellow-500 pl-4">
                <h3 className="font-medium text-gray-900">サービス改善</h3>
                <p className="text-gray-700">システムの安定性向上、ユーザー体験の改善</p>
              </div>

              <div className="border-l-4 border-red-500 pl-4">
                <h3 className="font-medium text-gray-900">法的義務の履行</h3>
                <p className="text-gray-700">法令に基づく報告、監査対応、紛争解決</p>
              </div>
            </div>
          </section>

          {/* セクション3: 第三者提供 */}
          <section id="section3" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">3. 個人情報の第三者提供</h2>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <p className="text-yellow-800">
                <strong>基本方針:</strong>
                ユーザーの同意なく個人情報を第三者に提供することはありません。
              </p>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">例外的な提供先</h3>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">提供先</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">提供する情報</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">目的</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">AWS（Amazon Web Services）</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">すべてのユーザーデータ</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">クラウドインフラ提供</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">法執行機関</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">法的要請に応じた範囲</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">法的義務の履行</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* セクション4: セキュリティ */}
          <section id="section4" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">4. 個人情報の保管・セキュリティ</h2>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">技術的対策</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-2">
                  <li>データベース暗号化（AES-256）</li>
                  <li>通信暗号化（HTTPS/TLS 1.2以上）</li>
                  <li>アクセス制御・認証システム</li>
                  <li>定期的なセキュリティ監査</li>
                </ul>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">組織的対策</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-2">
                  <li>アクセス権限の最小化</li>
                  <li>操作ログの記録・監視</li>
                  <li>インシデント対応手順</li>
                  <li>従業員教育・研修</li>
                </ul>
              </div>
            </div>
          </section>

          {/* セクション5: ユーザーの権利 */}
          <section id="section5" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">5. ユーザーの権利</h2>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-medium text-blue-900 mb-3">GDPR に基づく権利</h3>
              <p className="text-blue-800">EU居住者の方は、以下の権利を行使することができます。</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">アクセス権</h4>
                  <p className="text-sm text-gray-700">保存されている個人データの確認・取得</p>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">修正権</h4>
                  <p className="text-sm text-gray-700">不正確な個人データの修正要求</p>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">削除権</h4>
                  <p className="text-sm text-gray-700">個人データの削除要求（忘れられる権利）</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">処理制限権</h4>
                  <p className="text-sm text-gray-700">個人データ処理の制限要求</p>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">データポータビリティ権</h4>
                  <p className="text-sm text-gray-700">構造化されたデータの取得・移転</p>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">異議申立権</h4>
                  <p className="text-sm text-gray-700">データ処理に対する異議申立</p>
                </div>
              </div>
            </div>
          </section>

          {/* セクション6: Cookie */}
          <section id="section6" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">6. Cookie の使用</h2>

            <div className="space-y-6">
              <p className="text-gray-700">本サービスでは、サービス提供に必要な Cookie を使用します。</p>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cookie 種別</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">目的</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">保持期間</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">認証 Cookie</td>
                      <td className="px-6 py-4 text-sm text-gray-700">ログイン状態の維持</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">24時間</td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">セッション Cookie</td>
                      <td className="px-6 py-4 text-sm text-gray-700">セッション管理・セキュリティ</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">ブラウザ終了まで</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* セクション7: データ保持期間 */}
          <section id="section7" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">7. データ保持期間</h2>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">ユーザーアカウント情報</h3>
                <p className="text-gray-700">アカウント削除から7年間保持後、自動的に匿名化されます。</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">アクセスログ</h3>
                <p className="text-gray-700">セキュリティ監視目的で1年間保持後、自動削除されます。</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">監査ログ</h3>
                <p className="text-gray-700">法的要件により7年間保持されます。</p>
              </div>
            </div>
          </section>

          {/* セクション8: お問い合わせ */}
          <section id="section8" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">8. お問い合わせ</h2>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-blue-900 mb-4">個人情報保護に関するお問い合わせ</h3>

              <div className="space-y-3 text-blue-800">
                <p>
                  <strong>データ保護責任者:</strong> システム管理者
                </p>
                <p>
                  <strong>メールアドレス:</strong> privacy@example.com
                </p>
                <p>
                  <strong>対応時間:</strong> 平日 9:00-17:00（土日祝日を除く）
                </p>
                <p className="text-sm">※ お問い合わせには3営業日以内に回答いたします</p>
              </div>
            </div>
          </section>

          {/* フッター */}
          <div className="bg-white shadow rounded-lg p-6 text-center">
            <p className="text-gray-600 mb-4">
              このプライバシーポリシーは、法令の変更やサービスの改善に伴い更新される場合があります。 重要な変更がある場合は、事前にユーザーに通知いたします。
            </p>

            <div className="flex justify-center space-x-4">
              <Link href="/" className="text-blue-600 hover:text-blue-500">
                ホームに戻る
              </Link>
              <Link href="/terms" className="text-blue-600 hover:text-blue-500">
                利用規約
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PrivacyPolicyPage;
