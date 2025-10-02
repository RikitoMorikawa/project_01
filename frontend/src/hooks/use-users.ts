import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-client";
import { useNotifications } from "@/stores/ui-store";
import { User, UserCreate, UserUpdate, PaginatedResponse } from "@/types";

// ユーザーAPI関数
const usersApi = {
  // ユーザー一覧取得
  getUsers: async (params?: { page?: number; page_size?: number; search?: string }): Promise<PaginatedResponse<User>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append("page", params.page.toString());
    if (params?.page_size) searchParams.append("page_size", params.page_size.toString());
    if (params?.search) searchParams.append("search", params.search);

    const response = await apiClient.get<PaginatedResponse<User>>(`/api/v1/users?${searchParams.toString()}`);
    return response;
  },

  // ユーザー詳細取得
  getUser: async (id: number): Promise<User> => {
    const response = await apiClient.get<{ data: User }>(`/api/v1/users/${id}`);
    return response.data;
  },

  // ユーザー作成
  createUser: async (userData: UserCreate): Promise<User> => {
    const response = await apiClient.post<{ data: User }>("/api/v1/users", userData);
    return response.data;
  },

  // ユーザー更新
  updateUser: async ({ id, data }: { id: number; data: UserUpdate }): Promise<User> => {
    const response = await apiClient.put<{ data: User }>(`/api/v1/users/${id}`, data);
    return response.data;
  },

  // ユーザー削除
  deleteUser: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/users/${id}`);
  },
};

// ユーザー一覧フック
export const useUsers = (params?: { page?: number; page_size?: number; search?: string }) => {
  return useQuery({
    queryKey: queryKeys.users.list(params || {}),
    queryFn: () => usersApi.getUsers(params),
    staleTime: 2 * 60 * 1000, // 2分
  });
};

// ユーザー詳細フック
export const useUser = (id: number) => {
  return useQuery({
    queryKey: queryKeys.users.detail(id),
    queryFn: () => usersApi.getUser(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5分
  });
};

// ユーザー作成フック
export const useCreateUser = () => {
  const queryClient = useQueryClient();
  const notifications = useNotifications();

  return useMutation({
    mutationFn: usersApi.createUser,
    onSuccess: (newUser) => {
      // ユーザー一覧のキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });

      notifications.success("ユーザー作成完了", `${newUser.username} を作成しました`);
    },
    onError: (error: any) => {
      notifications.error("ユーザー作成エラー", error.message);
    },
  });
};

// ユーザー更新フック
export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  const notifications = useNotifications();

  return useMutation({
    mutationFn: usersApi.updateUser,
    onSuccess: (updatedUser) => {
      // 関連するキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.users.detail(updatedUser.id) });

      notifications.success("ユーザー更新完了", `${updatedUser.username} を更新しました`);
    },
    onError: (error: any) => {
      notifications.error("ユーザー更新エラー", error.message);
    },
  });
};

// ユーザー削除フック
export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  const notifications = useNotifications();

  return useMutation({
    mutationFn: usersApi.deleteUser,
    onSuccess: (_, deletedUserId) => {
      // 関連するキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
      queryClient.removeQueries({ queryKey: queryKeys.users.detail(deletedUserId) });

      notifications.success("ユーザー削除完了", "ユーザーを削除しました");
    },
    onError: (error: any) => {
      notifications.error("ユーザー削除エラー", error.message);
    },
  });
};
