import React from "react";
import { Field, PageTitle, Info } from "../../components/common";
import { userApi } from "../../services/api";
import { writeUser } from "../../app/storage";

export function ProfilePage({ role, user, notify }) {
  const [editing, setEditing] = React.useState(false);
  const [passwordOpen, setPasswordOpen] = React.useState(false);
  const [form, setForm] = React.useState({
    name: user?.name || "",
    nickname: user?.nickname || "",
  });
  const [password, setPassword] = React.useState({
    oldPassword: "",
    newPassword: "",
  });
  // 保存中状态：按钮转文案 + 禁用，避免连点提交两次
  const [savingProfile, setSavingProfile] = React.useState(false);
  const [savingPassword, setSavingPassword] = React.useState(false);
  const updateProfile = async (event) => {
    event.preventDefault();
    if (savingProfile) return;
    if (!form.name.trim() && !form.nickname.trim()) {
      return notify("姓名和昵称至少填一个", "error");
    }
    setSavingProfile(true);
    try {
      const next = await userApi.update(form);
      writeUser(next);
      notify("资料已更新", "success");
      setEditing(false);
    } catch (error) {
      notify(error, "error");
    } finally {
      setSavingProfile(false);
    }
  };
  const updatePassword = async (event) => {
    event.preventDefault();
    if (savingPassword) return;
    if (!password.oldPassword) return notify("请输入当前密码", "error");
    if (!password.newPassword) return notify("请输入新密码", "error");
    if (/[\u3400-\u9fff]/.test(password.newPassword))
      return notify("新密码不能包含中文", "error");
    if (password.newPassword === password.oldPassword)
      return notify("新密码不能与当前密码相同", "error");
    setSavingPassword(true);
    try {
      await userApi.password(password);
      notify("密码修改成功", "success");
      setPasswordOpen(false);
      setPassword({ oldPassword: "", newPassword: "" });
    } catch (error) {
      notify(error, "error");
    } finally {
      setSavingPassword(false);
    }
  };
  return (
    <div className="page">
      <PageTitle
        eyebrow="PROFILE"
        title="个人中心"
        desc="管理你的个人资料与账号安全。"
      />
      <div className="profile-grid">
        <section className="panel profile-card">
          <div className="profile-avatar">
            {(user?.nickname || user?.name || "U").slice(0, 1)}
          </div>
          <h2>{user?.nickname || user?.name || "用户"}</h2>
          <p>
            {role === "student" ? "学生" : "教师"} · {user?.account || "—"}
          </p>
          <button className="outline" onClick={() => setEditing(!editing)}>
            编辑资料
          </button>
        </section>
        <section className="panel profile-info">
          <h3>基础资料</h3>
          <Info label="账号" value={user?.account} />
          <Info label="姓名" value={user?.name} />
          <Info label="昵称" value={user?.nickname} />
          <Info label="手机号" value="—" />
          <Info label="邮箱" value="—" />
          <div className="info-actions">
            <button
              className="outline"
              onClick={() => setPasswordOpen(!passwordOpen)}
            >
              修改密码
            </button>
          </div>
        </section>
      </div>
      {editing && (
        <form className="panel form-panel" onSubmit={updateProfile}>
          <div className="form-grid">
            <Field
              label="姓名"
              value={form.name}
              onChange={(value) => setForm({ ...form, name: value })}
            />
            <Field
              label="昵称"
              value={form.nickname}
              onChange={(value) => setForm({ ...form, nickname: value })}
            />
          </div>
          <button className="primary" disabled={savingProfile}>
            {savingProfile ? "保存中…" : "保存资料"}
          </button>
        </form>
      )}
      {passwordOpen && (
        <form className="panel form-panel" onSubmit={updatePassword}>
          <div className="form-grid">
            <Field
              label="旧密码"
              type="password"
              required
              value={password.oldPassword}
              onChange={(value) =>
                setPassword({ ...password, oldPassword: value })
              }
            />
            <Field
              label="新密码"
              type="password"
              required
              value={password.newPassword}
              onChange={(value) =>
                setPassword({ ...password, newPassword: value })
              }
            />
          </div>
          <button className="primary" disabled={savingPassword}>
            {savingPassword ? "提交中…" : "确认修改密码"}
          </button>
        </form>
      )}
    </div>
  );
}
