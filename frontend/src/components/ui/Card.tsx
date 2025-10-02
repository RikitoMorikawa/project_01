import React from "react";

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  shadow?: "none" | "sm" | "md" | "lg";
}

const Card: React.FC<CardProps> = ({ children, className = "", padding = "md", shadow = "md" }) => {
  const baseClasses = "bg-white rounded-lg border border-gray-200";

  const paddingClasses = {
    none: "",
    sm: "p-3",
    md: "p-4",
    lg: "p-6",
  };

  const shadowClasses = {
    none: "",
    sm: "shadow-sm",
    md: "shadow",
    lg: "shadow-lg",
  };

  const classes = [baseClasses, paddingClasses[padding], shadowClasses[shadow], className].filter(Boolean).join(" ");

  return <div className={classes}>{children}</div>;
};

export default Card;
