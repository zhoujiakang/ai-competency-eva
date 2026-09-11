import React, { useState } from "react";
import { ArrowRight } from "lucide-react";
import { authApi, classApi } from "../../services/api";
import { saveToken } from "../../app/storage";
import { Field } from "../../components/common";

export function AuthPage({ mode, role, back, register, onLogin, notify }) {
  const [form, setForm] = useState({
    account: "",
    password: "",
    name: "",
    nickname: "",
    phone: "",
    email: "",
    inviteCode: "",
  });
  const [loading, setLoading] = useState(false);
  const update = (key, value) => setForm({ ...form, [key]: value });
  const submit = async (event) => {
    event.preventDefault();
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
        await authApi.register(role, form);
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
            notify("注册成功，组织码无效，可在「我的班级」重新加入");
          }
        } else {
          notify("注册成功");
        }
        onLogin?.(data.user, role);
      }
    } catch (error) {
      notify(error.message);
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
          <form onSubmit={submit}>
            {mode === "register" && (
              <>
                <Field
                  label="姓名"
                  value={form.name}
                  onChange={(value) => update("name", value)}
                  required
                />
                <Field
                  label="昵称"
                  value={form.nickname}
                  onChange={(value) => update("nickname", value)}
                  required
                />
              </>
            )}
            <Field
              label="账号"
              value={form.account}
              onChange={(value) => update("account", value)}
              required
            />
            <Field
              label="密码"
              type="password"
              value={form.password}
              onChange={(value) => update("password", value)}
              required
            />
            {mode === "register" && (
              <>
                <Field
                  label="手机号"
                  value={form.phone}
                  onChange={(value) => update("phone", value)}
                />
                <Field
                  label="邮箱（可选）"
                  value={form.email}
                  onChange={(value) => update("email", value)}
                />
                {role === "student" && (
                  <>
                    <Field
                      label="组织码（选填）"
                      value={form.inviteCode}
                      onChange={(value) => update("inviteCode", value)}
                    />
                    <small className="field-hint">选填，填写后自动加入该班级</small>
                  </>
                )}
              </>
            )}
            <button className="primary full" disabled={loading}>
              {loading ? "处理中…" : mode === "login" ? "登录" : "注册"}{" "}
              <ArrowRight size={16} />
            </button>
          </form>
          <div className="auth-foot">
            {mode === "login" ? (
              <>
                <button
                  className="text-btn"
                  onClick={() => notify("忘记密码功能暂未开放")}
                >
                  忘记密码？
                </button>
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
