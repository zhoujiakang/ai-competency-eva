import React, { useEffect } from "react";
import { X } from "lucide-react";

export function Feature({ num, icon, title, text }) {
  return (
    <div className="feature">
      <div className="feature-top">
        <span>{num}</span>
        {icon}
      </div>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
export function Field({
  label,
  value,
  onChange,
  type = "text",
  required,
  error,
  hint,
  placeholder,
  autoComplete,
}) {
  return (
    <label className={`field${error ? " has-error" : ""}`}>
      <span>
        {label}
        {required && " *"}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        autoComplete={autoComplete}
        aria-invalid={error ? "true" : undefined}
      />
      {error && <small className="field-error">{error}</small>}
      {!error && hint && <small className="field-hint">{hint}</small>}
    </label>
  );
}
export function PageTitle({ eyebrow, title, desc, action }) {
  return (
    <div className="page-title">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        {desc && <p>{desc}</p>}
      </div>
      {action}
    </div>
  );
}
export function Stat({ value, label, muted = false }) {
  return (
    <div className={`stat ${muted ? "muted-stat" : ""}`}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
export function Empty({ icon, text, action, onAction }) {
  return (
    <div className="empty">
      {icon}
      <p>{text}</p>
      {action && (
        <button className="outline" onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  );
}
export function Info({ label, value }) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

/**
 * 通用弹窗：点遮罩或按 Esc 关闭，打开时锁定页面滚动。
 * footer 用来放「取消 / 确认」这类操作。
 */
export function Modal({ title, description, children, footer, onClose, wide = false }) {
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKeyDown);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose?.();
      }}
    >
      <div className={`modal${wide ? " modal-wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head">
          <div>
            <h3>{title}</h3>
            {description && <p>{description}</p>}
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="关闭"
          >
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}
