import { create } from "zustand";
import { devtools } from "zustand/middleware";

// UI状態の型定義
interface UiState {
  // 状態
  sidebarOpen: boolean;
  theme: "light" | "dark" | "system";
  notifications: Notification[];
  loading: Record<string, boolean>;

  // アクション
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  addNotification: (notification: Omit<Notification, "id">) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  setLoading: (key: string, loading: boolean) => void;
  clearLoading: (key: string) => void;
}

// 通知の型定義
interface Notification {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// UIストア
export const useUiStore = create<UiState>()(
  devtools(
    (set, get) => ({
      // 初期状態
      sidebarOpen: false,
      theme: "system",
      notifications: [],
      loading: {},

      // サイドバートグル
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen }), false, "ui/toggleSidebar"),

      // サイドバー開閉設定
      setSidebarOpen: (open) => set({ sidebarOpen: open }, false, "ui/setSidebarOpen"),

      // テーマ設定
      setTheme: (theme) => set({ theme }, false, "ui/setTheme"),

      // 通知追加
      addNotification: (notification) => {
        const id = Math.random().toString(36).substr(2, 9);
        const newNotification: Notification = {
          ...notification,
          id,
          duration: notification.duration || 5000,
        };

        set(
          (state) => ({
            notifications: [...state.notifications, newNotification],
          }),
          false,
          "ui/addNotification"
        );

        // 自動削除
        if (newNotification.duration && newNotification.duration > 0) {
          setTimeout(() => {
            get().removeNotification(id);
          }, newNotification.duration);
        }
      },

      // 通知削除
      removeNotification: (id) =>
        set(
          (state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }),
          false,
          "ui/removeNotification"
        ),

      // 全通知クリア
      clearNotifications: () => set({ notifications: [] }, false, "ui/clearNotifications"),

      // ローディング状態設定
      setLoading: (key, loading) =>
        set(
          (state) => ({
            loading: {
              ...state.loading,
              [key]: loading,
            },
          }),
          false,
          "ui/setLoading"
        ),

      // ローディング状態クリア
      clearLoading: (key) =>
        set(
          (state) => {
            const { [key]: _, ...rest } = state.loading;
            return { loading: rest };
          },
          false,
          "ui/clearLoading"
        ),
    }),
    {
      name: "ui-store",
    }
  )
);

// 通知用のヘルパー関数
export const useNotifications = () => {
  const { addNotification } = useUiStore();

  return {
    success: (title: string, message?: string) => addNotification({ type: "success", title, message }),
    error: (title: string, message?: string) => addNotification({ type: "error", title, message }),
    warning: (title: string, message?: string) => addNotification({ type: "warning", title, message }),
    info: (title: string, message?: string) => addNotification({ type: "info", title, message }),
  };
};
