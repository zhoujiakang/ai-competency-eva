import React, { useState } from "react";
import { ArrowRight } from "lucide-react";
import { authApi, classApi } from "../../services/api";
import { saveToken } from "../../app/storage";
import { Field } from "../../components/common";

export function AuthPage({ mode, role, back, register, onLogin, notify }) {
  const [form, setForm] = useState({
    account: "",
    password: "",
    confirmPassword: "",
    name: "",
    nickname: "",
    phone: "",
    email: "",
    inviteCode: "",
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  // 表单级错误：直接显示在按钮上方，不依赖提示条——
  // 即使提示条没看到或被关掉，用户也一定知道"为什么没登录进去"。
  const [formError, setFormError] = useState("");

  const update = (key, value) => {
    setForm((previous) => ({ ...previous, [key]: value }));
    // 用户开始改这个字段，就把它和表单级的报错一起清掉
    setErrors((previous) => (previous[key] ? { ...previous, [key]: "" } : previous));
    setFormError("");
  };

  /** 前端先校验一轮，规则与后端一致：必填、密码不含中文、手机号格式。 */
  const validate = () => {
    const next = {};
    if (!form.account.trim()) next.account = "请输入账号";
    if (!form.password) next.password = "请输入密码";
    else if (/[\u3400-\u9fff]/.test(form.password)) next.password = "密码不能包含中文";
    if (mode === "register") {
      if (form.password && form.password !== form.confirmPassword)
        next.confirmPassword = "两次输入的密码不一致";
      if (!form.name.trim()) next.name = "请输入姓名";
      if (!form.nickname.trim()) next.nickname = "请输入昵称";
      if (form.phone.trim() && !/^\d{11}$/.test(form.phone.trim()))
        next.phone = "手机号应为 11 位数字";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (event) => {
    event.preventDefault();
    setFormError("");
    if (!validate()) {
      setFormError("请先修正上面标注的问题");
      return;
    }
    setLoading(true);
    try {
      if (mode === "login") {
        const data = await authApi.login({
          account: form.account,
          password: form.password,
          role,
        });
        saveToken(data.tokenValue);
        onLogin(data.user, role);
      } else {
        // 只提交后端认识的字段（确认密码、组织码都不是注册接口的参数）
        await authApi.register(role, {
          account: form.account.trim(),
          password: form.password,
          name: form.name.trim(),
          nickname: form.nickname.trim(),
          phone: form.phone.trim(),
          email: form.email.trim(),
        });
        // 注册成功后先完成登录拿到令牌——加入班级（join）需要登录态。
        const data = await authApi.login({
          account: form.account,
          password: form.password,
          role,
        });
        saveToken(data.tokenValue);
        const code = (form.inviteCode || "").trim();
        if (role === "student" && code) {
          try {
            const classroom = await classApi.join(code);
            notify(`注册成功，已加入「${classroom?.name || "班级"}」`);
          } catch {
            // 组织码填错不阻断注册：账号已经建好，稍后可以在「我的班级」重新加入。
            notify("注册成功，组织码无效，可在「我的班级」重新加入", "info");
          }
        } else {
          notify("注册成功", "success");
        }
        onLogin?.(data.user, role);
      }
    } catch (error) {
      // 两条通道同时给：按钮上方的内联提示 + 全局提示条
      setFormError(error.message || "操作失败，请重试");
      notify(error, "error");
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="auth-page">
      <div className="auth-side">
        <div className="brand">
          <span className="brand-mark">✦</span> AI 能力测评
        </div>
        <div>
          <div className="eyebrow">
            {role === "student" ? "STUDENT SPACE" : "TEACHER SPACE"}
          </div>
          <h1>
            {role === "student"
              ? "把你的想法，\n说出来。"
              : "让每一次教学，\n更接近真实。"}
          </h1>
          <p>与 AI 测评官进行一场有来有往的对话。</p>
        </div>
      </div>
      <div className="auth-card-wrap">
        <button className="back-link" onClick={back}>
          ← 返回
        </button>
        <div className="auth-card">
          <div className="eyebrow">
            {mode === "login" ? "WELCOME BACK" : "CREATE ACCOUNT"}
          </div>
          <h2>{mode === "login" ? "欢迎回来" : "创建你的账号"}</h2>
          <p className="muted">
            {role === "student" ? "学生端" : "教师端"} ·{" "}
            {mode === "login" ? "登录后继续你的测评旅程" : "注册后开始使用平台"}
          </p>
          {/* noValidate：关掉浏览器原生校验气泡，统一由下面的 validate() 给字段级提示，
              否则空字段时用户看到的是浏览器自带的提示，样式与文案都不受控 */}
          <form onSubmit={submit} noValidate>
            {mode === "register" && (
              <>
                <Field
                  label="姓名"
                  value={form.name}
                  onChange={(value) => update("name", value)}
                  required
                  error={errors.name}
                  autoComplete="name"
                />
                <Field
                  label="昵称"
                  value={form.nickname}
                  onChange={(value) => update("nickname", value)}
                  required
                  error={errors.nickname}
                  autoComplete="nickname"
                />
              </>
            )}
            <Field
              label="账号"
              value={form.account}
              onChange={(value) => update("account", value)}
              required
              error={errors.account}
              autoComplete="username"
            />
            <Field
              label="密码"
              type="password"
              value={form.password}
              onChange={(value) => update("password", value)}
              required
              error={errors.password}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
            {mode === "register" && (
              <>
                <Field
                  label="确认密码"
                  type="password"
                  value={form.confirmPassword}
                  onChange={(value) => update("confirmPassword", value)}
                  required
                  error={errors.confirmPassword}
                  autoComplete="new-password"
                />
                <Field
                  label="手机号"
                  value={form.phone}
                  onChange={(value) => update("phone", value)}
                  error={errors.phone}
                  hint="选填，11 位数字"
                  autoComplete="tel"
                />
                <Field
                  label="邮箱（可选）"
                  value={form.email}
                  onChange={(value) => update("email", value)}
                  autoComplete="email"
                />
                {role === "student" && (
                  <Field
                    label="组织码（选填）"
                    value={form.inviteCode}
                    onChange={(value) => update("inviteCode", value)}
                    hint="选填，填写后自动加入该班级"
                  />
                )}
              </>
            )}
            {formError && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}
            <button className="primary full" disabled={loading}>
              {loading ? "处理中…" : mode === "login" ? "登录" : "注册"}{" "}
              <ArrowRight size={16} />
            </button>
          </form>
          <div className="auth-foot">
            {mode === "login" ? (
              <>
                <button className="text-btn" onClick={register}>
                  注册新账号
                </button>
              </>
            ) : (
              <button className="text-btn" onClick={register}>
                已有账号？返回登录
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
