// User related types
export interface User {
  id: number;
  cognitoUserId: string;
  email: string;
  username: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile {
  id: number;
  userId: number;
  firstName?: string;
  lastName?: string;
  avatarUrl?: string;
  bio?: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: "success" | "error";
}

// Authentication types
export interface LoginCredentials {
  email: string;
  password: string;
}

// User management types
export interface UserCreate {
  email: string;
  username: string;
  password: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
}

// Pagination types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuthContext {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  getToken: () => Promise<string | null>;
}

// API client types
export interface RequestConfig {
  headers?: Record<string, string>;
  timeout?: number;
}

export interface ApiClient {
  get<T>(endpoint: string, config?: RequestConfig): Promise<T>;
  post<T>(endpoint: string, data: any, config?: RequestConfig): Promise<T>;
  put<T>(endpoint: string, data: any, config?: RequestConfig): Promise<T>;
  delete<T>(endpoint: string, config?: RequestConfig): Promise<T>;
}

// Error types
export class ApiError extends Error {
  constructor(public errorCode: string, public message: string, public statusCode: number, public details?: any) {
    super(message);
  }
}
