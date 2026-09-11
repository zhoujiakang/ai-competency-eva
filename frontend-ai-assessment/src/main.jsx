import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import "./styles.css";

class AppErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error) {
    console.error("前端运行错误", error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="app-error">
          <h1>页面加载失败</h1>
          <p>{this.state.error.message || "前端发生未知错误"}</p>
          <button onClick={() => window.location.reload()}>刷新页面</button>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  <AppErrorBoundary>
    <App />
  </AppErrorBoundary>,
);
