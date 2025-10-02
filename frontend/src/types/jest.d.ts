/**
 * Jest型定義ファイル
 * Jest type definitions
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveTextContent(text: string | RegExp): R;
      toHaveAttribute(attr: string, value?: string): R;
      toBeDisabled(): R;
      toBeRequired(): R;
    }
  }
}

export {};
