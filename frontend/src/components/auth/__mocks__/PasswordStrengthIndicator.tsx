/**
 * PasswordStrengthIndicatorコンポーネントのモック
 * Mock for PasswordStrengthIndicator component
 */

import React from "react";

interface PasswordStrengthIndicatorProps {
  password: string;
}

const PasswordStrengthIndicator: React.FC<PasswordStrengthIndicatorProps> = ({ password }) => {
  return (
    <div data-testid="password-strength-indicator">
      <div>パスワード強度: {password.length >= 8 ? "強" : "弱"}</div>
    </div>
  );
};

export default PasswordStrengthIndicator;
