import React from "react";

export interface PasswordStrengthIndicatorProps {
  password: string;
  showDetails?: boolean;
}

interface PasswordCriteria {
  label: string;
  test: (password: string) => boolean;
}

const PasswordStrengthIndicator: React.FC<PasswordStrengthIndicatorProps> = ({ password, showDetails = true }) => {
  const criteria: PasswordCriteria[] = [
    { label: "8文字以上", test: (pwd) => pwd.length >= 8 },
    { label: "大文字を含む", test: (pwd) => /[A-Z]/.test(pwd) },
    { label: "小文字を含む", test: (pwd) => /[a-z]/.test(pwd) },
    { label: "数字を含む", test: (pwd) => /\d/.test(pwd) },
    { label: "特殊文字を含む", test: (pwd) => /[@$!%*?&]/.test(pwd) },
  ];

  const passedCriteria = criteria.filter((criterion) => criterion.test(password));
  const strength = passedCriteria.length;

  const getStrengthColor = () => {
    if (strength <= 1) return "bg-red-500";
    if (strength <= 2) return "bg-orange-500";
    if (strength <= 3) return "bg-yellow-500";
    if (strength <= 4) return "bg-blue-500";
    return "bg-green-500";
  };

  const getStrengthText = () => {
    if (strength <= 1) return "弱い";
    if (strength <= 2) return "やや弱い";
    if (strength <= 3) return "普通";
    if (strength <= 4) return "強い";
    return "とても強い";
  };

  if (!password) return null;

  return (
    <div className="mt-2">
      {/* 強度バー */}
      <div className="flex items-center space-x-2 mb-2">
        <span className="text-xs text-gray-600">パスワード強度:</span>
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div className={`h-2 rounded-full transition-all duration-300 ${getStrengthColor()}`} style={{ width: `${(strength / criteria.length) * 100}%` }} />
        </div>
        <span className={`text-xs font-medium ${strength >= 4 ? "text-green-600" : strength >= 3 ? "text-yellow-600" : "text-red-600"}`}>
          {getStrengthText()}
        </span>
      </div>

      {/* 詳細な条件 */}
      {showDetails && (
        <div className="space-y-1">
          {criteria.map((criterion, index) => {
            const passed = criterion.test(password);
            return (
              <div key={index} className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full flex items-center justify-center ${passed ? "bg-green-500" : "bg-gray-300"}`}>
                  {passed && (
                    <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <span className={`text-xs ${passed ? "text-green-600" : "text-gray-500"}`}>{criterion.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PasswordStrengthIndicator;
