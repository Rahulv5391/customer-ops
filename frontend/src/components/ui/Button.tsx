import { Spinner } from './Spinner';
import type { ReactNode, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
  loading?: boolean;
  children: ReactNode;
}

const variantClasses = {
  primary: 'btn-primary', secondary: 'btn-secondary',
  danger: 'btn-danger',   ghost: 'btn-ghost',
};
const sizeClasses = { sm: 'text-xs px-2.5 py-1.5', md: '' };

export function Button({ variant = 'primary', size = 'md', loading = false, children, disabled, className = '', ...props }: ButtonProps) {
  return (
    <button {...props} disabled={disabled || loading} className={`${variantClasses[variant]} ${sizeClasses[size]} ${className}`}>
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
}
