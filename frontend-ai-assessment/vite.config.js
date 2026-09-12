import { defineConfig } from "vite";

/**
 * 构建配置：只做一件事——把基本不变的第三方库拆成独立 chunk。
 *
 * 应用代码每次发布都会变，react / lucide 很少变；拆开之后用户再次访问时
 * 只需要重新下载应用代码那一小块，其余继续走浏览器缓存。
 *
 * 页面级的懒加载在 App.jsx 里用 React.lazy 声明，不需要在这里配。
 */
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        // Vite 8 底层是 rolldown，manualChunks 只接受函数形式。
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("lucide-react")) return "icons";
          if (id.includes("react") || id.includes("scheduler")) return "react";
          return undefined;
        },
      },
    },
  },
});
