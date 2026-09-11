import { reportClientLog } from "../services/api";

/**
 * 前端错误上报。
 *
 * 浏览器里的异常只弹给用户是不够的：现场出问题时，开发者手里只有一句
 * "打不开"。这里把异常送到后端，落到服务端日志里，可以这样查：
 *
 *     ssh root@<服务器> 'journalctl -u ai-assessment-backend | grep 前端错误'
 *
 * 三条自律（避免把日志刷爆，也避免上报本身变成新的故障源）：
 *   · 同一类错误（kind + 页面 + 文案）只报一次；
 *   · 每次会话最多上报 20 条；
 *   · 上报失败静默忽略，不再触发新的上报。
 */
const MAX_PER_SESSION = 20;
const reported = new Set();

export function reportError(error, context = {}) {
  try {
    const message = String(error?.message || error || "").trim().slice(0, 500);
    if (!message) return;
    const kind = context.kind || "error";
    const page = window.location.pathname + window.location.search;
    const key = `${kind}|${page}|${message}`;
    if (reported.has(key) || reported.size >= MAX_PER_SESSION) return;
    reported.add(key);
    reportClientLog({
      kind,
      message,
      stack: String(error?.stack || "").slice(0, 2000),
      url: page,
      userAgent: navigator.userAgent.slice(0, 200),
    });
  } catch {
    // 上报失败绝不能影响用户
  }
}

/** 兜住没人处理的异常：Promise 拒绝与运行时错误。 */
export function installGlobalErrorReporting() {
  window.addEventListener("error", (event) => {
    if (event?.error) reportError(event.error, { kind: "runtime" });
    else if (event?.message) reportError(new Error(event.message), { kind: "resource" });
  });
  window.addEventListener("unhandledrejection", (event) => {
    reportError(event?.reason || new Error("未处理的 Promise 拒绝"), { kind: "promise" });
  });
}
