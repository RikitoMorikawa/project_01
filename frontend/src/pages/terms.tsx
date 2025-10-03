/**
 * 利用規約ページ
 *
 * サービス利用に関する規約・条件を表示
 * 法的要件に準拠した利用規約
 */

import React from "react";
import Head from "next/head";
import Link from "next/link";

const TermsOfServicePage: React.FC = () => {
  return (
    <>
      <Head>
        <title>利用規約 | CSR Lambda API システム</title>
        <meta name="description" content="CSR Lambda API システムの利用規約・サービス利用条件" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* ヘッダー */}
          <div className="bg-white shadow rounded-lg p-8 mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">利用規約</h1>
            <p className="text-gray-600 mb-4">最終更新日: 2024年1月1日 | バージョン: 1.0</p>
            <p className="text-gray-700">
              この利用規約（以下「本規約」）は、CSR Lambda API システム（以下「本サービス」）の
              利用条件を定めるものです。本サービスをご利用になる場合には、本規約にご同意いただく必要があります。
            </p>
          </div>

          {/* 目次 */}
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">目次</h2>
            <nav className="grid md:grid-cols-2 gap-2">
              <a href="#article1" className="block text-blue-600 hover:text-blue-500">
                第1条 定義
              </a>
              <a href="#article2" className="block text-blue-600 hover:text-blue-500">
                第2条 本規約への同意
              </a>
              <a href="#article3" className="block text-blue-600 hover:text-blue-500">
                第3条 アカウント登録
              </a>
              <a href="#article4" className="block text-blue-600 hover:text-blue-500">
                第4条 サービスの利用
              </a>
              <a href="#article5" className="block text-blue-600 hover:text-blue-500">
                第5条 禁止事項
              </a>
              <a href="#article6" className="block text-blue-600 hover:text-blue-500">
                第6条 個人情報の取扱い
              </a>
              <a href="#article7" className="block text-blue-600 hover:text-blue-500">
                第7条 知的財産権
              </a>
              <a href="#article8" className="block text-blue-600 hover:text-blue-500">
                第8条 免責事項
              </a>
              <a href="#article9" className="block text-blue-600 hover:text-blue-500">
                第9条 サービスの変更・停止
              </a>
              <a href="#article10" className="block text-blue-600 hover:text-blue-500">
                第10条 規約の変更
              </a>
            </nav>
          </div>

          {/* 第1条 定義 */}
          <section id="article1" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第1条（定義）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">本規約において使用する用語の定義は、次のとおりとします。</p>

              <div className="space-y-3">
                <div className="border-l-4 border-blue-500 pl-4">
                  <h3 className="font-medium text-gray-900">「本サービス」</h3>
                  <p className="text-gray-700">CSR Lambda API システムおよび関連するすべてのサービス</p>
                </div>

                <div className="border-l-4 border-green-500 pl-4">
                  <h3 className="font-medium text-gray-900">「ユーザー」</h3>
                  <p className="text-gray-700">本サービスを利用する個人または法人</p>
                </div>

                <div className="border-l-4 border-yellow-500 pl-4">
                  <h3 className="font-medium text-gray-900">「アカウント」</h3>
                  <p className="text-gray-700">本サービス利用のために作成されるユーザー固有の利用権</p>
                </div>

                <div className="border-l-4 border-red-500 pl-4">
                  <h3 className="font-medium text-gray-900">「コンテンツ」</h3>
                  <p className="text-gray-700">本サービス上で提供される文章、画像、動画、その他の情報</p>
                </div>
              </div>
            </div>
          </section>

          {/* 第2条 本規約への同意 */}
          <section id="article2" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第2条（本規約への同意）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. ユーザーは、本規約の内容を承諾した上で本サービスを利用するものとします。</p>
              <p className="text-gray-700">2. 本規約に同意しない場合、ユーザーは本サービスを利用することができません。</p>
              <p className="text-gray-700">3. 未成年者が本サービスを利用する場合、親権者の同意が必要です。</p>
            </div>
          </section>

          {/* 第3条 アカウント登録 */}
          <section id="article3" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第3条（アカウント登録）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. 本サービスの利用には、アカウント登録が必要です。</p>
              <p className="text-gray-700">2. 登録時に提供する情報は、正確かつ最新のものである必要があります。</p>
              <p className="text-gray-700">3. ユーザーは、アカウント情報の管理について全責任を負います。</p>
              <p className="text-gray-700">4. アカウントの不正利用を発見した場合、直ちに当社に報告してください。</p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-6">
              <h3 className="font-medium text-yellow-800 mb-2">登録要件</h3>
              <ul className="list-disc list-inside text-yellow-700 space-y-1">
                <li>有効なメールアドレスの提供</li>
                <li>安全なパスワードの設定</li>
                <li>利用規約およびプライバシーポリシーへの同意</li>
              </ul>
            </div>
          </section>

          {/* 第4条 サービスの利用 */}
          <section id="article4" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第4条（サービスの利用）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. ユーザーは、本規約に従って本サービスを利用するものとします。</p>
              <p className="text-gray-700">2. 本サービスは、個人的かつ非商業的な目的でのみ利用できます。</p>
              <p className="text-gray-700">3. ユーザーは、本サービスの正常な運営を妨げる行為を行ってはなりません。</p>
            </div>
          </section>

          {/* 第5条 禁止事項 */}
          <section id="article5" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第5条（禁止事項）</h2>

            <div className="space-y-4">
              <p className="text-gray-700 mb-4">ユーザーは、本サービスの利用にあたり、以下の行為を行ってはなりません。</p>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <h4 className="font-medium text-red-800">法令違反行為</h4>
                    <p className="text-sm text-red-700">法律、規則、条例等に違反する行為</p>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <h4 className="font-medium text-red-800">不正アクセス</h4>
                    <p className="text-sm text-red-700">システムへの不正侵入やハッキング行為</p>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <h4 className="font-medium text-red-800">迷惑行為</h4>
                    <p className="text-sm text-red-700">他のユーザーや第三者への迷惑行為</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <h4 className="font-medium text-red-800">知的財産権侵害</h4>
                    <p className="text-sm text-red-700">著作権、商標権等の侵害行為</p>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <h4 className="font-medium text-red-800">虚偽情報の提供</h4>
                    <p className="text-sm text-red-700">虚偽または誤解を招く情報の提供</p>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <h4 className="font-medium text-red-800">商業利用</h4>
                    <p className="text-sm text-red-700">事前承諾のない商業目的での利用</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 第6条 個人情報の取扱い */}
          <section id="article6" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第6条（個人情報の取扱い）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">
                1. 個人情報の取扱いについては、別途定める
                <Link href="/privacy" className="text-blue-600 hover:text-blue-500 mx-1">
                  プライバシーポリシー
                </Link>
                に従います。
              </p>
              <p className="text-gray-700">2. ユーザーは、プライバシーポリシーの内容を理解し、同意するものとします。</p>
              <p className="text-gray-700">3. 個人情報の取扱いに関する問い合わせは、所定の窓口で受け付けます。</p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
              <h3 className="font-medium text-blue-800 mb-2">データ保護の取り組み</h3>
              <ul className="list-disc list-inside text-blue-700 space-y-1">
                <li>GDPR および個人情報保護法への準拠</li>
                <li>データの暗号化と安全な保管</li>
                <li>ユーザーの権利（アクセス、修正、削除等）の保障</li>
                <li>定期的なセキュリティ監査の実施</li>
              </ul>
            </div>
          </section>

          {/* 第7条 知的財産権 */}
          <section id="article7" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第7条（知的財産権）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. 本サービスに関する知的財産権は、当社または正当な権利者に帰属します。</p>
              <p className="text-gray-700">2. ユーザーが投稿したコンテンツの著作権は、ユーザーに帰属します。</p>
              <p className="text-gray-700">3. ユーザーは、投稿コンテンツについて、当社に利用許諾を与えるものとします。</p>
            </div>
          </section>

          {/* 第8条 免責事項 */}
          <section id="article8" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第8条（免責事項）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. 当社は、本サービスの完全性、正確性、安全性を保証するものではありません。</p>
              <p className="text-gray-700">2. 本サービスの利用により生じた損害について、当社は責任を負いません。</p>
              <p className="text-gray-700">3. システム障害、メンテナンス等によるサービス停止について、当社は責任を負いません。</p>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-6">
              <h3 className="font-medium text-gray-800 mb-2">免責対象</h3>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>天災、事変、その他の不可抗力による損害</li>
                <li>第三者による不正アクセスやサイバー攻撃</li>
                <li>ユーザーの過失による損害</li>
                <li>予期しないシステム障害やデータ消失</li>
              </ul>
            </div>
          </section>

          {/* 第9条 サービスの変更・停止 */}
          <section id="article9" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第9条（サービスの変更・停止）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. 当社は、ユーザーに事前に通知することなく、本サービスの内容を変更できます。</p>
              <p className="text-gray-700">2. 当社は、以下の場合、本サービスを一時的に停止できます。</p>

              <div className="ml-6 space-y-2">
                <p className="text-gray-700">• システムメンテナンスを行う場合</p>
                <p className="text-gray-700">• 緊急事態が発生した場合</p>
                <p className="text-gray-700">• その他、運営上必要と判断した場合</p>
              </div>

              <p className="text-gray-700">3. サービス停止により生じた損害について、当社は責任を負いません。</p>
            </div>
          </section>

          {/* 第10条 規約の変更 */}
          <section id="article10" className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">第10条（規約の変更）</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. 当社は、必要に応じて本規約を変更することができます。</p>
              <p className="text-gray-700">2. 規約変更の場合、変更内容を本サービス上で通知します。</p>
              <p className="text-gray-700">3. 変更後の規約は、通知から30日経過後に効力を生じます。</p>
              <p className="text-gray-700">4. 変更に同意しない場合、ユーザーはアカウントを削除できます。</p>
            </div>
          </section>

          {/* 附則 */}
          <section className="bg-white shadow rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">附則</h2>

            <div className="space-y-4">
              <p className="text-gray-700">1. 本規約は、2024年1月1日から施行します。</p>
              <p className="text-gray-700">2. 本規約に関する準拠法は日本法とし、管轄裁判所は東京地方裁判所とします。</p>
              <p className="text-gray-700">3. 本規約の一部が無効となった場合でも、他の条項の効力には影響しません。</p>
            </div>
          </section>

          {/* フッター */}
          <div className="bg-white shadow rounded-lg p-6 text-center">
            <p className="text-gray-600 mb-4">ご不明な点がございましたら、お気軽にお問い合わせください。</p>

            <div className="flex justify-center space-x-4">
              <Link href="/" className="text-blue-600 hover:text-blue-500">
                ホームに戻る
              </Link>
              <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
                プライバシーポリシー
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TermsOfServicePage;
