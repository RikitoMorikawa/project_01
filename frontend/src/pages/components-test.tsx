import React from "react";
import { Layout } from "@/components/layout";
import ComponentShowcase from "@/components/ui/ComponentShowcase";

/**
 * コンポーネントテストページ
 * 開発時にUIコンポーネントの動作確認用
 */
const ComponentsTestPage: React.FC = () => {
  return (
    <Layout
      title="UI コンポーネント テスト | CSR Lambda API"
      description="UI コンポーネントの動作確認ページ"
      headerProps={{
        title: "CSR Lambda API",
        showAuth: false,
        showNavigation: true,
      }}
    >
      <div className="py-8">
        <ComponentShowcase />
      </div>
    </Layout>
  );
};

export default ComponentsTestPage;
