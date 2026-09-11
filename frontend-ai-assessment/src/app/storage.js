const keys = {
  token: "assessment_token",
  user: "assessment_user",
  role: "assessment_role",
  assessment: "current_assessment",
  selectedClass: "selected_class",
};

export const readToken = () => localStorage.getItem(keys.token);
export const saveToken = (token) =>
  token
    ? localStorage.setItem(keys.token, token)
    : localStorage.removeItem(keys.token);
export const readRole = () => localStorage.getItem(keys.role);
export const readUser = () => {
  try {
    return JSON.parse(localStorage.getItem(keys.user) || "null");
  } catch {
    return null;
  }
};
export const writeUser = (user) =>
  localStorage.setItem(keys.user, JSON.stringify(user));
export const writeRole = (role) => localStorage.setItem(keys.role, role);
export const writeCurrentAssessment = (assessment) =>
  localStorage.setItem(keys.assessment, JSON.stringify(assessment));
export const removeCurrentAssessment = () =>
  localStorage.removeItem(keys.assessment);
export const readCurrentAssessment = () => {
  try {
    return JSON.parse(localStorage.getItem(keys.assessment) || "null");
  } catch {
    return null;
  }
};
export const writeSelectedClass = (classroom) =>
  (() => {
    if (classroom) localStorage.setItem(keys.selectedClass, JSON.stringify(classroom));
    else localStorage.removeItem(keys.selectedClass);
    window.dispatchEvent(new CustomEvent("selected-class-changed", { detail: classroom }));
  })();
export const readSelectedClass = () => {
  try {
    return JSON.parse(localStorage.getItem(keys.selectedClass) || "null");
  } catch {
    return null;
  }
};
export const clearSession = () =>
  [keys.token, keys.user, keys.role, keys.selectedClass].forEach((key) =>
    localStorage.removeItem(key),
  );
