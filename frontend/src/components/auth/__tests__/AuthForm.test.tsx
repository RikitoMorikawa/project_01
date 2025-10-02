/**
 * AuthFormコンポーネントの単体テスト
 * Unit tests for AuthForm component
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from "react";
import { render, screen, fireEvent, waitFor } from "@/__tests__/utils/test-utils";
import AuthForm, { AuthFormProps } from "../AuthForm";

// テスト用のデフォルトプロパティ / Default props for testing
const defaultProps: AuthFormProps = {
  type: "login",
  onSubmit: jest.fn(),
  loading: false,
};

describe("AuthForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("ログインフォーム / Login Form", () => {
    it("ログインフォームが正しくレンダリングされる / Login form renders correctly", () => {
      render(<AuthForm {...defaultProps} type="login" />);

      expect(screen.getByText("ログイン")).toBeInTheDocument();
      expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "ログイン" })).toBeInTheDocument();
    });

    it("有効なデータでフォーム送信が実行される / Form submission works with valid data", async () => {
      const mockOnSubmit = jest.fn().mockResolvedValue(undefined);

      render(<AuthForm {...defaultProps} onSubmit={mockOnSubmit} />);

      // フォームに入力 / Fill form
      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "password123" } });

      // フォーム送信 / Submit form
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          email: "test@example.com",
          password: "password123",
        });
      });
    });

    it("メールアドレスが空の場合にバリデーションエラーが表示される / Validation error shows for empty email", async () => {
      render(<AuthForm {...defaultProps} />);

      // パスワードのみ入力 / Enter password only
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "password123" } });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      await waitFor(() => {
        expect(screen.getByText("メールアドレスを入力してください")).toBeInTheDocument();
      });
    });

    it("無効なメールアドレス形式でバリデーションエラーが表示される / Validation error shows for invalid email format", async () => {
      render(<AuthForm {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "invalid-email" } });
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "password123" } });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      await waitFor(() => {
        expect(screen.getByText("有効なメールアドレスを入力してください")).toBeInTheDocument();
      });
    });

    it("パスワードが空の場合にバリデーションエラーが表示される / Validation error shows for empty password", async () => {
      render(<AuthForm {...defaultProps} />);

      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      await waitFor(() => {
        expect(screen.getByText("パスワードを入力してください")).toBeInTheDocument();
      });
    });
  });

  describe("登録フォーム / Register Form", () => {
    it("登録フォームが正しくレンダリングされる / Register form renders correctly", () => {
      render(<AuthForm {...defaultProps} type="register" />);

      expect(screen.getByText("アカウント作成")).toBeInTheDocument();
      expect(screen.getByLabelText("ユーザー名")).toBeInTheDocument();
      expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード確認")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "アカウントを作成" })).toBeInTheDocument();
    });

    it("有効なデータで登録フォーム送信が実行される / Register form submission works with valid data", async () => {
      const mockOnSubmit = jest.fn().mockResolvedValue(undefined);

      render(<AuthForm {...defaultProps} type="register" onSubmit={mockOnSubmit} />);

      // フォームに入力 / Fill form
      fireEvent.change(screen.getByLabelText("ユーザー名"), { target: { value: "testuser" } });
      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "password123" } });
      fireEvent.change(screen.getByLabelText("パスワード確認"), { target: { value: "password123" } });

      // 利用規約に同意 / Agree to terms
      fireEvent.click(screen.getByLabelText("利用規約とプライバシーポリシーに同意します"));

      // フォーム送信 / Submit form
      fireEvent.click(screen.getByRole("button", { name: "アカウントを作成" }));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          username: "testuser",
          email: "test@example.com",
          password: "password123",
          confirmPassword: "password123",
        });
      });
    });

    it("ユーザー名が短すぎる場合にバリデーションエラーが表示される / Validation error shows for username too short", async () => {
      render(<AuthForm {...defaultProps} type="register" />);

      fireEvent.change(screen.getByLabelText("ユーザー名"), { target: { value: "ab" } });
      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "password123" } });
      fireEvent.change(screen.getByLabelText("パスワード確認"), { target: { value: "password123" } });
      fireEvent.click(screen.getByRole("button", { name: "アカウントを作成" }));

      await waitFor(() => {
        expect(screen.getByText("ユーザー名は3文字以上で入力してください")).toBeInTheDocument();
      });
    });

    it("パスワードが短すぎる場合にバリデーションエラーが表示される / Validation error shows for password too short", async () => {
      render(<AuthForm {...defaultProps} type="register" />);

      fireEvent.change(screen.getByLabelText("ユーザー名"), { target: { value: "testuser" } });
      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "123" } });
      fireEvent.change(screen.getByLabelText("パスワード確認"), { target: { value: "123" } });
      fireEvent.click(screen.getByRole("button", { name: "アカウントを作成" }));

      await waitFor(() => {
        expect(screen.getByText("パスワードは8文字以上で入力してください")).toBeInTheDocument();
      });
    });

    it("パスワード確認が一致しない場合にバリデーションエラーが表示される / Validation error shows for password mismatch", async () => {
      render(<AuthForm {...defaultProps} type="register" />);

      fireEvent.change(screen.getByLabelText("ユーザー名"), { target: { value: "testuser" } });
      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText("パスワード"), { target: { value: "password123" } });
      fireEvent.change(screen.getByLabelText("パスワード確認"), { target: { value: "different123" } });
      fireEvent.click(screen.getByRole("button", { name: "アカウントを作成" }));

      await waitFor(() => {
        expect(screen.getByText("パスワードが一致しません")).toBeInTheDocument();
      });
    });
  });

  describe("パスワードリセットフォーム / Password Reset Form", () => {
    it("パスワードリセット要求フォームが正しくレンダリングされる / Password reset request form renders correctly", () => {
      render(<AuthForm {...defaultProps} type="forgot-password" />);

      expect(screen.getByText("パスワードリセット")).toBeInTheDocument();
      expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "リセットコードを送信" })).toBeInTheDocument();
      expect(screen.queryByLabelText("パスワード")).not.toBeInTheDocument();
    });

    it("パスワードリセット確認フォームが正しくレンダリングされる / Password reset confirmation form renders correctly", () => {
      render(<AuthForm {...defaultProps} type="reset-password" />);

      expect(screen.getByText("新しいパスワード設定")).toBeInTheDocument();
      expect(screen.getByLabelText("確認コード")).toBeInTheDocument();
      expect(screen.getByLabelText("新しいパスワード")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード確認")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "パスワードを変更" })).toBeInTheDocument();
      expect(screen.queryByLabelText("メールアドレス")).not.toBeInTheDocument();
    });
  });

  describe("プロパティとオプション / Props and Options", () => {
    it("ローディング状態が正しく表示される / Loading state displays correctly", () => {
      render(<AuthForm {...defaultProps} loading={true} />);

      const submitButton = screen.getByRole("button", { name: "ログイン" });
      expect(submitButton).toBeDisabled();
    });

    it("エラーメッセージが正しく表示される / Error message displays correctly", () => {
      const errorMessage = "ログインに失敗しました";
      render(<AuthForm {...defaultProps} error={errorMessage} />);

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it("成功メッセージが正しく表示される / Success message displays correctly", () => {
      const successMessage = "ログインに成功しました";
      render(<AuthForm {...defaultProps} success={successMessage} />);

      expect(screen.getByText(successMessage)).toBeInTheDocument();
    });

    it("初期データが正しく設定される / Initial data is set correctly", () => {
      const initialData = { email: "preset@example.com" };
      render(<AuthForm {...defaultProps} initialData={initialData} />);

      const emailInput = screen.getByLabelText("メールアドレス") as HTMLInputElement;
      expect(emailInput.value).toBe("preset@example.com");
    });

    it("パスワード強度インジケーターが表示される / Password strength indicator shows when enabled", () => {
      render(<AuthForm {...defaultProps} type="register" showPasswordStrength={true} />);

      // パスワード入力後にインジケーターが表示されることを確認
      // Verify indicator appears after password input
      const passwordInput = screen.getByLabelText("パスワード");
      fireEvent.change(passwordInput, { target: { value: "test123" } });

      // パスワード強度インジケーターコンポーネントがレンダリングされることを確認
      // Verify password strength indicator component is rendered
      expect(screen.getByTestId("password-strength-indicator")).toBeInTheDocument();
    });
  });

  describe("入力フィールドの動作 / Input Field Behavior", () => {
    it("入力値の変更が正しく処理される / Input value changes are handled correctly", async () => {
      render(<AuthForm {...defaultProps} />);

      const emailInput = screen.getByLabelText("メールアドレス") as HTMLInputElement;
      fireEvent.change(emailInput, { target: { value: "test@example.com" } });

      expect(emailInput.value).toBe("test@example.com");
    });

    it("エラーが表示された後に入力するとエラーがクリアされる / Error clears when typing after validation error", async () => {
      render(<AuthForm {...defaultProps} />);

      // バリデーションエラーを発生させる / Trigger validation error
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      await waitFor(() => {
        expect(screen.getByText("メールアドレスを入力してください")).toBeInTheDocument();
      });

      // 入力するとエラーがクリアされる / Error clears when typing
      fireEvent.change(screen.getByLabelText("メールアドレス"), { target: { value: "test@example.com" } });

      await waitFor(() => {
        expect(screen.queryByText("メールアドレスを入力してください")).not.toBeInTheDocument();
      });
    });
  });

  describe("アクセシビリティ / Accessibility", () => {
    it("フォームラベルが正しく関連付けられている / Form labels are properly associated", () => {
      render(<AuthForm {...defaultProps} />);

      const emailInput = screen.getByLabelText("メールアドレス");
      const passwordInput = screen.getByLabelText("パスワード");

      expect(emailInput).toHaveAttribute("name", "email");
      expect(passwordInput).toHaveAttribute("name", "password");
    });

    it("必須フィールドが適切にマークされている / Required fields are properly marked", () => {
      render(<AuthForm {...defaultProps} type="register" />);

      const termsCheckbox = screen.getByLabelText("利用規約とプライバシーポリシーに同意します");
      expect(termsCheckbox).toBeRequired();
    });

    it("オートコンプリート属性が正しく設定されている / Autocomplete attributes are set correctly", () => {
      render(<AuthForm {...defaultProps} />);

      const emailInput = screen.getByLabelText("メールアドレス");
      const passwordInput = screen.getByLabelText("パスワード");

      expect(emailInput).toHaveAttribute("autoComplete", "email");
      expect(passwordInput).toHaveAttribute("autoComplete", "current-password");
    });
  });
});
