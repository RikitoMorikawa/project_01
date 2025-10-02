import type { AppProps } from "next/app";
import "@/styles/globals.css";
import { AppProvider } from "@/providers/app-provider";
import Notification from "@/components/ui/Notification";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AppProvider>
      <Component {...pageProps} />
      <Notification />
    </AppProvider>
  );
}
