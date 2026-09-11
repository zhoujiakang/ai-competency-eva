/**
 * 词表（taxonomy）取值工具。
 *
 * 后端已把 points 从「字符串数组」升级为「{ name, description } 数组」
 * （对应《具体考察点2.0》）。这里集中做兼容取值，页面里就不用到处判断类型，
 * 老接口如果还返回字符串也不会崩。
 */
export const pointName = (point) =>
  typeof point === "string" ? point : point?.name || "";

export const pointDescription = (point) =>
  typeof point === "string" ? "" : point?.description || "";

export const pointNames = (group) =>
  (group?.points || []).map(pointName).filter(Boolean);

export const findGroup = (taxonomy, dimension) =>
  (taxonomy || []).find((group) => group.dimension === dimension) || null;

/** 题目上的 JSON 数组字段（`tags` / `assessmentPoints`）统一按这个解析。 */
const parseList = (value) => {
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [];
  }
};

/** 题目可以属于多个维度，tags 存的就是维度数组。 */
export const questionDimensions = (question) => parseList(question?.tags);

/** 题目上的考察点数组（编辑题目时回填表单用）。 */
export const questionAssessmentPoints = (question) => parseList(question?.assessmentPoints);

export const questionDimensionLabel = (question) => {
  const dimensions = questionDimensions(question);
  return dimensions.length ? dimensions.join(" / ") : "—";
};
