import React from "react";
import Button from "./Button";

export interface ErrorDisplayProps {
  title?: string;
  message?: string;
  error?: Error | string;
  type?: "inline" | "page" | "card";
  showRetry?: boolean;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
  children?: React.ReactNode;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title = "エラーが発生しました",
  message,
  error,
  type = "inline",
  showRetry = false,
  onRetry,
  retryLabel = "再試行",
  className = "",
  children,
}) => {
  // エラーメッセージの取得
  const getErrorMessage = () => {
    if (message) return message;
    if (typeof error === "string") return error;
    if (error instanceof Error) return error.message;
    return "予期しないエラーが発生しました。";
  };

  // エラーアイコン
  const ErrorIcon = () => (
    <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  );

  // インラインエラー表示
  if (type === "inline") {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-md p-4 ${className}`}>
        <div className="flex">
          <div className="flex-shrink-0">
            <ErrorIcon />
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-red-800">{title}</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{getErrorMessage()}</p>
            </div>
            {(showRetry || children) && (
              <div className="mt-4">
                <div className="flex space-x-3">
                  {showRetry && onRetry && (
                    <Button variant="outline" size="sm" onClick={onRetry}>
                      {retryLabel}
                    </Button>
                  )}
                  {children}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // カードエラー表示
  if (type === "card") {
    return (
      <div className={`bg-white border border-red-200 rounded-lg shadow-sm p-6 ${className}`}>
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <ErrorIcon />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
          <p className="text-sm text-gray-600 mb-4">{getErrorMessage()}</p>
          {(showRetry || children) && (
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {showRetry && onRetry && (
                <Button variant="primary" onClick={onRetry}>
                  {retryLabel}
                </Button>
              )}
              {children}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ページエラー表示
  return (
    <div className={`min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-6">
            <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900 mb-4">{title}</h2>
          <p className="text-lg text-gray-600 mb-8">{getErrorMessage()}</p>
          {(showRetry || children) && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {showRetry && onRetry && (
                <Button variant="primary" size="lg" onClick={onRetry}>
                  {retryLabel}
                </Button>
              )}
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;
