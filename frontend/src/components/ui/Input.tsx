import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
}

const Input: React.FC<InputProps> = ({ label, error, helperText, fullWidth = false, startIcon, endIcon, className = "", id, ...props }) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  const baseClasses = "px-3 py-2 border rounded-md transition focus-ring";
  const stateClasses = error ? "border-red-500 focus:border-red-500" : "border-gray-300 focus:border-blue-500";
  const widthClass = fullWidth ? "w-full" : "";
  const iconPaddingClass = startIcon ? "pl-10" : endIcon ? "pr-10" : "";

  const inputClasses = [baseClasses, stateClasses, widthClass, iconPaddingClass, className].filter(Boolean).join(" ");

  return (
    <div className={fullWidth ? "w-full" : ""}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}

      <div className="relative">
        {startIcon && <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">{startIcon}</div>}

        <input id={inputId} className={inputClasses} {...props} />

        {endIcon && <div className="absolute inset-y-0 right-0 pr-3 flex items-center">{endIcon}</div>}
      </div>

      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}

      {helperText && !error && <p className="mt-1 text-sm text-gray-500">{helperText}</p>}
    </div>
  );
};

export default Input;
