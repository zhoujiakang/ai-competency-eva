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
  const updateProfile = async (event) => {
    event.preventDefault();
    try {
      const next = await userApi.update(form);
      writeUser(next);
      notify("资料已更新");
      setEditing(false);
    } catch (error) {
      notify(error.message);
    }
  };
  const updatePassword = async (event) => {
    event.preventDefault();
    try {
      await userApi.password(password);
      notify("密码修改成功");
      setPasswordOpen(false);
      setPassword({ oldPassword: "", newPassword: "" });
    } catch (error) {
      notify(error.message);
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
          <button className="primary">保存资料</button>
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
          <button className="primary">确认修改密码</button>
        </form>
      )}
    </div>
  );
}
