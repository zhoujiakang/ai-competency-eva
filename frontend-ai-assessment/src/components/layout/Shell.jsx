import React, { useEffect, useState } from "react";
import { ChevronRight, LogOut, Menu } from "lucide-react";
import { getNavigation } from "../../app/navigation";
import { classApi } from "../../services/api";
import { readSelectedClass, writeSelectedClass } from "../../app/storage";

export function Shell({ role, user, screen, go, logout, toast, children }) {
  const items = getNavigation(role);
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(readSelectedClass);
  useEffect(() => {
    if (role !== "student") return;
    classApi.joined().then((items) => {
      setClasses(items);
      const saved = items.find((item) => item.id === selectedClass?.id) || items[0] || null;
      setSelectedClass(saved);
      writeSelectedClass(saved);
    }).catch(() => setClasses([]));
  }, [role]);
  const selectClass = (id) => {
    const next = classes.find((item) => String(item.id) === String(id)) || null;
    setSelectedClass(next);
    writeSelectedClass(next);
  };
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">✦</span> AI 能力测评
        </div>
        <div className="role-label">
          {role === "student" ? "STUDENT" : "TEACHER"} SPACE
        </div>
        <nav>
          {items.map(([id, label, Icon]) => (
            <button
              key={id}
              className={screen === id ? "active" : ""}
              onClick={() => go(id)}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          {role === "student" && <label className="current-class-picker">
            <span>当前班级</span>
            <select value={selectedClass?.id || ""} onChange={(event) => selectClass(event.target.value)}>
              <option value="">请选择班级</option>
              {classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>}
          <div className="sidebar-user-row">
            <div className="user-mini">
              <div className="avatar">
                {(user?.nickname || user?.name || "U").slice(0, 1)}
              </div>
              <div>
                <strong>{user?.nickname || user?.name || "用户"}</strong>
                <small>{user?.account || "已登录"}</small>
              </div>
            </div>
            <button
              className="logout-icon"
              onClick={logout}
              aria-label="退出登录"
              title="退出登录"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <main className={`content ${screen === "assessment" ? "assessment-content" : ""}`}>
        <header className="topbar">
          <button className="mobile-menu">
            <Menu size={20} />
          </button>
          <span className="crumb">
            {role === "student" ? "学生端" : "教师端"}{" "}
            <ChevronRight size={14} />{" "}
            {items.find((x) => x[0] === screen)?.[1] || "测评"}
          </span>
          <div className="top-actions">
            <span className="status-dot" /> 系统运行中
          </div>
        </header>
        {children}
        {toast && (
          <div className="toast" role="status">
            {toast}
          </div>
        )}
      </main>
    </div>
  );
}
