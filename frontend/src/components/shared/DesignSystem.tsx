import {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  TextareaHTMLAttributes,
  forwardRef,
} from "react";

// ---- Button ---------------------------------------------------------------

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const btnVariant: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-600 hover:bg-brand-500 text-white border border-brand-500 disabled:bg-slate-700 disabled:text-slate-400 disabled:border-slate-700",
  secondary:
    "bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700",
  ghost:
    "bg-transparent hover:bg-slate-800 text-slate-300 border border-transparent",
  danger:
    "bg-red-600/90 hover:bg-red-500 text-white border border-red-500",
};

const btnSize: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "primary", size = "md", loading, className = "", children, ...rest },
    ref
  ) => (
    <button
      ref={ref}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-brand-500/40 ${btnVariant[variant]} ${btnSize[size]} ${className}`}
      disabled={loading || rest.disabled}
      {...rest}
    >
      {loading && (
        <span className="inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  )
);
Button.displayName = "Button";

// ---- Input ----------------------------------------------------------------

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className = "", ...rest }, ref) => (
  <input
    ref={ref}
    className={`w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition ${className}`}
    {...rest}
  />
));
Input.displayName = "Input";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className = "", ...rest }, ref) => (
  <textarea
    ref={ref}
    className={`w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition resize-none ${className}`}
    {...rest}
  />
));
Textarea.displayName = "Textarea";

// ---- ToggleSwitch ---------------------------------------------------------

export interface ToggleSwitchProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  label?: string;
}

export function ToggleSwitch({
  checked,
  onChange,
  disabled,
  label,
}: ToggleSwitchProps) {
  return (
    <label className={`inline-flex items-center gap-2 ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition ${
          checked ? "bg-brand-600" : "bg-slate-700"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : ""
          }`}
        />
      </button>
      {label && <span className="text-sm text-slate-300">{label}</span>}
    </label>
  );
}

// ---- Slider ---------------------------------------------------------------

export interface SliderProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (next: number) => void;
  disabled?: boolean;
}

export function Slider({
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  disabled,
}: SliderProps) {
  return (
    <div className="flex items-center gap-3">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 accent-brand-500"
      />
      <span className="text-xs text-slate-400 font-mono w-14 text-right">
        {value}
      </span>
    </div>
  );
}

// ---- Card -----------------------------------------------------------------

export function Card({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`bg-slate-900/60 border border-slate-800 rounded-xl ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 px-5 py-4 border-b border-slate-800">
      <div className="min-w-0">
        <h3 className="text-sm font-semibold text-slate-100 truncate">{title}</h3>
        {subtitle && (
          <p className="text-xs text-slate-400 mt-0.5 truncate">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

export function CardBody({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>;
}

// ---- FormField ------------------------------------------------------------

export interface FormFieldProps {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  required?: boolean;
  children: ReactNode;
}

export function FormField({
  label,
  hint,
  error,
  required,
  children,
}: FormFieldProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-xs font-medium text-slate-300">
          {label}
          {required && <span className="text-red-400 ml-0.5">*</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

// ---- Badge ----------------------------------------------------------------

export type BadgeTone = "default" | "success" | "warning" | "danger" | "brand";

const badgeTone: Record<BadgeTone, string> = {
  default: "bg-slate-800 text-slate-300 border-slate-700",
  success: "bg-green-950 text-green-300 border-green-800",
  warning: "bg-yellow-950 text-yellow-300 border-yellow-800",
  danger: "bg-red-950 text-red-300 border-red-800",
  brand: "bg-brand-600/20 text-brand-400 border-brand-600/40",
};

export function Badge({
  tone = "default",
  children,
}: {
  tone?: BadgeTone;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-md border ${badgeTone[tone]}`}
    >
      {children}
    </span>
  );
}