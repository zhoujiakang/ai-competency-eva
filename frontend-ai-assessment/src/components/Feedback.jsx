import React from "react";
import { AlertCircle, CheckCircle2, Info, Loader2, RefreshCw, X } from "lucide-react";

/**
 * 全局提示条。
 *
 * 挂在 App 的最外层，所以**任何页面**都能看到它——包括登录/注册页：
 * 之前提示只在 Shell 里渲染，而登录页不经过 Shell，导致「账号或密码错误」
 * 这类报错被静默丢掉。
 *
 * 三种语气：success（成功）、error（失败，停留更久）、info（一般说明）。
 */
const TOAST_ICON = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

export function ToastHost({ toasts, onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="toast-host" role="status" aria-live="polite">
      {toasts.map((item) => {
        const Icon = TOAST_ICON[item.type] || Info;
        return (
          <div className={`toast toast-${item.type}`} key={item.id}>
            <Icon size={17} />
            <span>{item.text}</span>
            <button
              type="button"
              className="toast-close"
              onClick={() => onDismiss(item.id)}
              aria-label="关闭提示"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

/** 页面级加载态：一句话 + 转圈，避免"还在加载"被误读成"没有数据"。 */
export function Loading({ text = "正在加载…" }) {
  return (
    <div className="state-block">
      <Loader2 className="spin" size={22} />
      <p>{text}</p>
    </div>
  );
}

/** 页面级错误态：说清哪里失败 + 给一个重试按钮，而不是显示成"没有数据"。 */
export function ErrorState({ message, onRetry, retryText = "重新加载" }) {
  return (
    <div className="state-block state-error">
      <AlertCircle size={22} />
      <p>{message || "加载失败"}</p>
      {onRetry && (
        <button type="button" className="outline" onClick={onRetry}>
          <RefreshCw size={14} /> {retryText}
        </button>
      )}
    </div>
  );
}

/**
 * 列表骨架屏。
 *
 * 比一句"正在加载…"更接近最终形态：布局先占好位，数据回来时就地替换，
 * 页面不会跳一下，用户也不会把"还没加载完"看成"没有数据"。
 * 纯装饰，对读屏软件隐藏。
 */
export function SkeletonList({ rows = 4, columns = 3 }) {
  const widths = ["42%", "18%", "12%", "10%"];
  return (
    <div className="skeleton skeleton-list" aria-hidden="true">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div className="skeleton-row" key={rowIndex}>
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <span
              className="skeleton-bar"
              key={columnIndex}
              style={{ width: widths[columnIndex] || "12%" }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/** 指标卡骨架：教师端任务页顶部那四个数字。 */
export function SkeletonStats({ count = 4 }) {
  return (
    <div className="skeleton skeleton-stats" aria-hidden="true">
      {Array.from({ length: count }).map((_, index) => (
        <div className="skeleton-card" key={index}>
          <span className="skeleton-bar" style={{ width: "58%" }} />
          <span className="skeleton-bar" style={{ width: "32%" }} />
        </div>
      ))}
    </div>
  );
}
