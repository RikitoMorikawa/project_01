import React, { useState } from "react";
import { Button, Input, Card, Loading, Form, ErrorDisplay } from "./index";

/**
 * UIコンポーネントのショーケース
 * 開発時の参考用コンポーネント
 */
const ComponentShowcase: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    // シミュレートされた API 呼び出し
    try {
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          if (Math.random() > 0.5) {
            resolve("成功");
          } else {
            reject(new Error("サーバーエラーが発生しました"));
          }
        }, 2000);
      });

      setSuccess("フォームが正常に送信されました！");
      setFormData({ name: "", email: "", message: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">UI コンポーネント ショーケース</h1>
        <p className="text-gray-600">開発で使用可能な UI コンポーネントの一覧です</p>
      </div>

      {/* ボタンコンポーネント */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">ボタンコンポーネント</h2>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <Button variant="primary">プライマリ</Button>
            <Button variant="secondary">セカンダリ</Button>
            <Button variant="outline">アウトライン</Button>
            <Button variant="ghost">ゴースト</Button>
            <Button variant="danger">危険</Button>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button size="sm">小</Button>
            <Button size="md">中</Button>
            <Button size="lg">大</Button>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button loading>ローディング中</Button>
            <Button disabled>無効</Button>
            <Button fullWidth>フル幅</Button>
          </div>
        </div>
      </Card>

      {/* 入力コンポーネント */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">入力コンポーネント</h2>
        <div className="space-y-4">
          <Input label="基本入力" placeholder="テキストを入力してください" />
          <Input label="エラー付き入力" error="このフィールドは必須です" placeholder="エラー状態の例" />
          <Input label="ヘルプテキスト付き" helperText="追加の説明テキストです" placeholder="ヘルプテキストの例" />
          <Input
            label="アイコン付き入力"
            placeholder="検索..."
            startIcon={
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
          />
        </div>
      </Card>

      {/* ローディングコンポーネント */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">ローディングコンポーネント</h2>
        <div className="flex items-center space-x-8">
          <div className="text-center">
            <Loading size="sm" />
            <p className="mt-2 text-sm text-gray-600">小</p>
          </div>
          <div className="text-center">
            <Loading size="md" text="読み込み中..." />
            <p className="mt-2 text-sm text-gray-600">中（テキスト付き）</p>
          </div>
          <div className="text-center">
            <Loading size="lg" />
            <p className="mt-2 text-sm text-gray-600">大</p>
          </div>
        </div>
      </Card>

      {/* エラー表示コンポーネント */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">エラー表示コンポーネント</h2>
        <div className="space-y-4">
          <ErrorDisplay
            type="inline"
            title="インラインエラー"
            message="これはインライン形式のエラー表示です"
            showRetry
            onRetry={() => alert("再試行がクリックされました")}
          />
          <ErrorDisplay
            type="card"
            title="カードエラー"
            message="これはカード形式のエラー表示です"
            showRetry
            onRetry={() => alert("再試行がクリックされました")}
          />
        </div>
      </Card>

      {/* フォームコンポーネント */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">フォームコンポーネント</h2>
        <Form
          title="お問い合わせフォーム"
          description="以下のフォームにご記入ください"
          onSubmit={handleSubmit}
          loading={loading}
          error={error || undefined}
          success={success || undefined}
          showCancelButton
          onCancel={() => {
            setFormData({ name: "", email: "", message: "" });
            setError(null);
            setSuccess(null);
          }}
        >
          <Input label="お名前" name="name" value={formData.name} onChange={handleInputChange} required fullWidth />
          <Input label="メールアドレス" name="email" type="email" value={formData.email} onChange={handleInputChange} required fullWidth />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">メッセージ</label>
            <textarea
              name="message"
              value={formData.message}
              onChange={handleInputChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="メッセージを入力してください"
              required
            />
          </div>
        </Form>
      </Card>

      {/* カードコンポーネント */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">カードコンポーネント</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card padding="sm" shadow="sm">
            <h3 className="font-medium">小さなカード</h3>
            <p className="text-sm text-gray-600 mt-1">小さなパディングとシャドウ</p>
          </Card>
          <Card padding="md" shadow="md">
            <h3 className="font-medium">中サイズカード</h3>
            <p className="text-sm text-gray-600 mt-1">中サイズのパディングとシャドウ</p>
          </Card>
          <Card padding="lg" shadow="lg">
            <h3 className="font-medium">大きなカード</h3>
            <p className="text-sm text-gray-600 mt-1">大きなパディングとシャドウ</p>
          </Card>
        </div>
      </Card>
    </div>
  );
};

export default ComponentShowcase;
