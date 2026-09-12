import js from "@eslint/js";
import globals from "globals";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

/**
 * 前端 lint 配置。
 *
 * 只开「能抓到真问题」的规则，不做代码风格审查（格式交给编辑器，避免满屏噪音）：
 *   · js.configs.recommended    未定义变量、不可达代码、重复 case、空 catch……
 *   · react/recommended         JSX 里的用法错误
 *   · react-hooks               hooks 调用位置与依赖数组——这类问题只在运行时炸
 *
 * 特意关掉的：
 *   · react/react-in-jsx-scope  新 JSX 转换不需要在每个文件 import React
 *   · react/prop-types          项目没有 prop-types 也没有 TS，开了只会满屏报错
 *   · no-empty 的 catch         这里有不少「尽力而为、失败就算了」的空 catch
 */
export default [
  { ignores: ["dist/**", "node_modules/**"] },
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    settings: { react: { version: "detect" } },
    plugins: { react, "react-hooks": reactHooks },
    rules: {
      ...react.configs.flat.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "no-empty": ["error", { allowEmptyCatch: true }],
      "no-unused-vars": ["error", { args: "after-used", argsIgnorePattern: "^_" }],
    },
  },
  {
    // 构建脚本跑在 Node 里，认得 process / __dirname 这类全局变量
    files: ["*.config.js"],
    languageOptions: { globals: { ...globals.node } },
  },
];
