import React from "react";
import Button from "./Button";
import Loading from "./Loading";

export interface FormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  children: React.ReactNode;
  title?: string;
  description?: string;
  loading?: boolean;
  error?: string;
  success?: string;
  submitLabel?: string;
  cancelLabel?: string;
  onCancel?: () => void;
  showSubmitButton?: boolean;
  showCancelButton?: boolean;
  submitButtonProps?: React.ComponentProps<typeof Button>;
  cancelButtonProps?: React.ComponentProps<typeof Button>;
}

const Form: React.FC<FormProps> = ({
  children,
  title,
  description,
  loading = false,
  error,
  success,
  submitLabel = "送信",
  cancelLabel = "キャンセル",
  onCancel,
  showSubmitButton = true,
  showCancelButton = false,
  submitButtonProps = {},
  cancelButtonProps = {},
  className = "",
  ...props
}) => {
  return (
    <form className={`space-y-6 ${className}`} {...props}>
      {/* フォームヘッダー */}
      {(title || description) && (
        <div className="text-center">
          {title && <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>}
          {description && <p className="text-gray-600">{description}</p>}
        </div>
      )}

      {/* エラーメッセージ */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* 成功メッセージ */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}

      {/* フォームコンテンツ */}
      <div className="space-y-4">{children}</div>

      {/* フォームアクション */}
      {(showSubmitButton || showCancelButton) && (
        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          {showSubmitButton && (
            <Button type="submit" loading={loading} disabled={loading} fullWidth={!showCancelButton} {...submitButtonProps}>
              {submitLabel}
            </Button>
          )}
          {showCancelButton && (
            <Button type="button" variant="outline" onClick={onCancel} disabled={loading} fullWidth={!showSubmitButton} {...cancelButtonProps}>
              {cancelLabel}
            </Button>
          )}
        </div>
      )}

      {/* ローディング表示 */}
      {loading && (
        <div className="flex justify-center">
          <Loading size="sm" text="処理中..." />
        </div>
      )}
    </form>
  );
};

export default Form;
