/**
 * 教师端页面的统一出口。
 *
 * 页面按职责拆成三个文件，这里只做转发，调用方（App.jsx）的导入路径保持不变：

 *   TeacherClassesPage.jsx    班级：邀请码、成员、班级题库
 *   TeacherQuestionsPage.jsx  题库：建题 / 改题 / 发布 / 下线 / 复制
 *   TeacherTasksPage.jsx      任务：发布测评任务、查看学生完成情况
 */
export { TeacherClassesPage } from "./TeacherClassesPage";
export { TeacherQuestionsPage } from "./TeacherQuestionsPage";
export { TeacherTasksPage } from "./TeacherTasksPage";
