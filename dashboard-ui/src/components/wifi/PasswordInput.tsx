"use client";

import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

interface PasswordInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string | null;
  minLength?: number;
}

export function PasswordInput({
  value,
  onChange,
  placeholder = "Enter password",
  disabled,
  error,
  minLength = 8,
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  const isValid = value.length >= minLength;
  const showError = error || (value.length > 0 && !isValid);

  return (
    <div className="space-y-2">
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2">
          <Lock className="h-4 w-4 text-muted-foreground" />
        </div>
        <input
          type={showPassword ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "w-full pl-10 pr-12 py-3 rounded-lg",
            "bg-card border border-border",
            "text-foreground placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            showError && "border-destructive focus:ring-destructive/50"
          )}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          disabled={disabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          {showPassword ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>
      {showError && (
        <p className="text-xs text-destructive">
          {error || `Password must be at least ${minLength} characters`}
        </p>
      )}
    </div>
  );
}
