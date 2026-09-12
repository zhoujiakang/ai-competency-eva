import React, { useEffect, useState } from "react";
import { ChevronRight, LogOut, Menu } from "lucide-react";
import { getNavigation } from "../../app/navigation";
import { classApi } from "../../services/api";
import { readSelectedClass, writeSelectedClass } from "../../app/storage";

/**
 * 登录后的外壳：侧边栏 + 顶栏 + 内容区。
 *
 * 提示条不在这里渲染——它挂在 App 最外层（components/Feedback.jsx），
 * 这样登录页、注册页也能看到报错。这里只负责导航、当前班级与连接状态。
 */
export function Shell({ role, user, screen, go, logout, notify, children }) {
  const items = getNavigation(role);
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(readSelectedClass);
  const [menuOpen, setMenuOpen] = useState(false);
  const [online, setOnline] = useState(true);

  useEffect(() => {
    if (role !== "student") return;
    classApi
      .joined()
      .then((items) => {
        setClasses(items);
        // 这里读 storage 里的当前选择，而不是读 selectedClass 这个 state：
        // 这个 effect 只该在角色变化时跑一次，把 state 写进依赖会让每次切换班级都重拉列表。
        const saved =
          items.find((item) => item.id === readSelectedClass()?.id) || items[0] || null;
        setSelectedClass(saved);
        writeSelectedClass(saved);
      })
      .catch((error) => {
        // 之前这里是静默的：加载失败时学生只看到空的班级下拉，不知道发生了什么
        setClasses([]);
        notify?.(error, "error");
      });
  }, [role, notify]);

  // 后端可达性：由 api 层的真实请求结果驱动，不再写死「系统运行中」
  useEffect(() => {
    const onStatus = (event) => setOnline(event.detail !== "offline");
    window.addEventListener("api-status", onStatus);
    return () => window.removeEventListener("api-status", onStatus);
  }, []);

  // 切换页面后收起移动端侧边栏
  useEffect(() => setMenuOpen(false), [screen]);

  const selectClass = (id) => {
    const next = classes.find((item) => String(item.id) === String(id)) || null;
    setSelectedClass(next);
    writeSelectedClass(next);
  };

  return (
    <div className={`app-shell${menuOpen ? " menu-open" : ""}`}>
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
              onClick={() => {
                setMenuOpen(false);
                go(id);
              }}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          {role === "student" && (
            <label className="current-class-picker">
              <span>当前班级</span>
              <select
                value={selectedClass?.id || ""}
                onChange={(event) => selectClass(event.target.value)}
              >
                <option value="">请选择班级</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
          )}
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
      <main
        className={`content ${screen === "assessment" ? "assessment-content" : ""}`}
      >
        <header className="topbar">
          <button
            className="mobile-menu"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label={menuOpen ? "收起导航" : "展开导航"}
            aria-expanded={menuOpen}
          >
            <Menu size={20} />
          </button>
          <span className="crumb">
            {role === "student" ? "学生端" : "教师端"} <ChevronRight size={14} />{" "}
            {items.find((x) => x[0] === screen)?.[1] || "测评"}
          </span>
          <div className={`top-actions${online ? "" : " offline"}`}>
            <span className="status-dot" /> {online ? "服务正常" : "连接异常"}
          </div>
        </header>
        {children}
      </main>
      {menuOpen && (
        <button
          type="button"
          className="sidebar-mask"
          aria-label="收起导航"
          onClick={() => setMenuOpen(false)}
        />
      )}
    </div>
  );
}
