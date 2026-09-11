import { readToken, saveToken, clearSession } from "../app/storage";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8080/api";

export async function request(path, options = {}) {
  const token = readToken();
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: token } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await response.json().catch(() => ({ message: "网络异常" }));
  if (response.status === 401 || body.code === 401) {
    saveToken();
    clearSession();
    window.location.reload();
    throw new Error("登录已过期，请重新登录");
  }
  if (!response.ok || (body.code && body.code !== 200))
    throw new Error(body.message || "请求失败");
  return body.data ?? body;
}
export const post = (path, body) =>
  request(path, { method: "POST", body: JSON.stringify(body) });
export const put = (path, body) =>
  request(path, { method: "PUT", body: JSON.stringify(body) });

export const authApi = {
  login: (payload) => post("/auth/login", payload),
  register: (role, payload) => post(`/auth/register/${role}`, payload),
  logout: () => post("/auth/logout", {}),
};
export const userApi = {
  me: () => request("/users/me"),
  update: (payload) => put("/users/me", payload),
  password: (payload) => put("/users/password", payload),
};
export const classApi = {
  joined: () => request("/classes/joined"),
  managed: () => request("/classes/managed"),
  join: (inviteCode) => post("/classes/join", { inviteCode }),
  // 班级能力数据：一次拿到雷达图、技能树、趋势曲线、上一次对比需要的全部数据。
  myAbility: (classId) => request(`/classes/${classId}/my-ability`),
  create: (payload) => post("/classes", payload),
  detail: (id) => request(`/classes/${id}`),
  members: (id) => request(`/classes/${id}/members`),
  leave: (id) => request(`/classes/${id}/leave`, { method: "DELETE" }),
  tasks: (id) => request(`/classes/${id}/assessment-tasks`),
  addQuestion: (cid, qid) => post(`/classes/${cid}/questions/${qid}`, {}),
  questions: (id) => request(`/classes/${id}/questions`),
  removeMember: (id, studentId) => request(`/classes/${id}/members/${studentId}`, { method: "DELETE" }),
  removeQuestion: (id, questionId) => request(`/classes/${id}/questions/${questionId}`, { method: "DELETE" }),
  refreshInvite: (id) => post(`/classes/${id}/invite-code`, {}),
};
export const questionApi = {
  list: () => request("/questions"),
  create: (payload) => post("/questions", payload),
  update: (id, payload) => put(`/questions/${id}`, payload),
  publish: (id) => post(`/questions/${id}/publish`, {}),
  offline: (id) => post(`/questions/${id}/offline`, {}),
  restore: (id) => post(`/questions/${id}/restore`, {}),
  detail: (id) => request(`/questions/${id}`),
  publicList: () => request("/questions/public"),
  unpublish: (id) => post(`/questions/${id}/unpublish`, {}),
  copyPublic: (id) => post(`/questions/public/${id}/copy`, {}),
  // 固定分类词表：维度 + 该维度下的考察点，前端只能用这里返回的值。
  taxonomy: () => request("/questions/taxonomy"),
};
export const taskApi = {
  available: () => request("/assessment-tasks/available"),
  detail: (id) => request(`/assessment-tasks/${id}`),
  managed: (classId) => request(`/classes/${classId}/assessment-tasks`),
  start: (id) => post(`/assessment-tasks/${id}/start`, {}),
  create: (cid, payload) => post(`/classes/${cid}/assessment-tasks`, payload),
  // options 是学生自选的考察范围 { dimensions, assessmentPoints }；不传表示不限制。
  startSelf: (classId, options) => post(`/classes/${classId}/self-assessments/start`, options || {}),
};
export const teacherApi = {
  classResults: (classId) => request(`/teacher/classes/${classId}/results`),
  taskResults: (taskId) =>
    request(`/teacher/assessment-tasks/${taskId}/results`),
  detail: (id) => request(`/teacher/assessments/${id}`),
};
export const assessmentApi = {
  // 不带 classId 时返回全部记录（兼容老行为）；带上就只返回该班级的记录。
  list: (classId) => request(classId ? `/assessments?classId=${classId}` : "/assessments"),
  status: (id) => request(`/assessments/${id}`),
  // 恢复现场：整场对话消息 + 当前题目
  conversation: (id) => request(`/assessments/${id}/conversation`),
  complete: (id) => post(`/assessments/${id}/complete`, {}),
  /**
   * 测评中的对话：一个请求一个回合。
   * 事件由后端决定——question（当前题目）、delta（发言片段）、
   * answered（某题答完）、finished（整场结束）、error。
   */
  chat: async (id, content, onEvent) => {
    const token = readToken();
    const response = await fetch(
      `${API_BASE}/assessments/${id}/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(token ? { Authorization: token } : {}),
        },
        body: JSON.stringify({ content }),
      },
    );
    if (!response.ok || !response.body) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.message || "流式连接失败");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    const handle = (block) => {
      const eventName = block
        .split("\n")
        .find((line) => line.startsWith("event:"))
        ?.slice(6)
        .trim();
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");
      if (!eventName || !data) return;
      let payload;
      try {
        payload = JSON.parse(data);
      } catch {
        payload = data;
      }
      if (eventName === "error")
        throw new Error(typeof payload === "string" ? payload : payload?.message || "对话失败");
      onEvent?.(eventName, payload);
    };
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";
      blocks.forEach(handle);
    }
    if (buffer.trim()) handle(buffer);
  },
  result: (id) => request(`/assessments/${id}/result`),
};
