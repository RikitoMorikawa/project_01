import React from "react";
import Head from "next/head";
import Header, { HeaderProps } from "./Header";
import Footer, { FooterProps } from "./Footer";

export interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  headerProps?: Partial<HeaderProps>;
  footerProps?: Partial<FooterProps>;
  showHeader?: boolean;
  showFooter?: boolean;
  className?: string;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  title = "CSR Lambda API System",
  description = "Client-side rendered application with Lambda API backend",
  headerProps = {},
  footerProps = {},
  showHeader = true,
  showFooter = true,
  className = "",
}) => {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className={`min-h-screen flex flex-col ${className}`}>
        {showHeader && <Header {...headerProps} />}

        <main className="flex-1">{children}</main>

        {showFooter && <Footer {...footerProps} />}
      </div>
    </>
  );
};

export default Layout;
