import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, id, className = '', ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && <label htmlFor={id} className="label">{label}</label>}
      <input id={id} className={`input ${error ? 'border-red-400 focus:border-red-500' : ''} ${className}`} {...props} />
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
