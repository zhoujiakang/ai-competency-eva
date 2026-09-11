import React, { useEffect, useState } from "react";
import { ArrowRight, BookOpen, FileCheck2, Gauge, GraduationCap, Users } from "lucide-react";
import { classApi, taskApi, assessmentApi } from "../../services/api";
import { readSelectedClass, writeCurrentAssessment, writeSelectedClass } from "../../app/storage";
import { PageTitle } from "../../components/common";
import { useSelectedClass } from "../../components/AbilityOverview";

export function StudentClassesPage({ go, notify }) {
  const [classes, setClasses] = useState([]);
  const [code, setCode] = useState("");
  const load = () =>
    classApi
      .joined()
      .then(async (items) => {
        setClasses(items);
        const selected = items.find((item) => item.id === readSelectedClass()?.id) || items[0] || null;
        writeSelectedClass(selected);
      })
      .catch(() => setClasses([]));
  useEffect(() => {
    load();
  }, []);
  const join = async () => {
    try {
      await classApi.join(code);
      setCode("");
      notify("加入班级成功");
      load();
    } catch (error) {
      notify(error.message);
    }
  };
  const leave = async (id) => { try { await classApi.leave(id); notify("已退出班级"); load(); } catch (error) { notify(error.message); } };
  return (
    <div className="page">
      <PageTitle
        eyebrow="MY CLASSES"
        title="我的班级"
        desc="在这里加入或退出班级；选择当前班级后，从工作台开始测评。"
        action={
          <div className="join-inline">
            <input
              placeholder="输入邀请码"
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
            <button className="primary" onClick={join}>
              加入班级
            </button>
          </div>
        }
      />
      {classes.length ? (
        <div className="card-grid">
          {classes.map((item) => (
            <div className="class-card" key={item.id}>
              <div className="class-icon">
                <GraduationCap />
              </div>
              <div className="class-card-body">
                <h3>{item.name}</h3>
                <p>{item.description || "暂无班级说明"}</p>
                <button className="outline" onClick={() => leave(item.id)}>退出班级</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="large-empty">
          <Users size={30} />
          <h3>还没有加入班级</h3>
          <p>请向老师获取邀请码。</p>
          <div className="join-large">
            <input
              placeholder="输入 6 位邀请码"
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
            <button className="primary" onClick={join}>
              加入班级
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function StudentTasksPage({ go, notify }) {
  const [items, setItems] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  // 任务与「我的测评记录」一起取回，按 taskId 匹配出每个任务的状态。
  const load = () =>
    Promise.all([taskApi.available().catch(() => []), assessmentApi.list().catch(() => [])])
      .then(([tasks, rows]) => {
        setItems(tasks);
        setRecords(rows);
      })
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  const DONE = ["completed", "completed_with_scoring_failure"];
  // 一人一次：一个任务只对应一条测评记录，完成后不再出现在待完成里。
  const rows = items.map((task) => {
    const mine = records.find((row) => String(row.taskId) === String(task.id));
    const status = !mine ? "todo" : DONE.includes(mine.status) ? "done" : "doing";
    return { task, mine, status };
  });
  const pending = rows.filter((row) => row.status !== "done");
  // 待完成的排在前面，已完成的沉底
  const ordered = [...rows].sort(
    (a, b) => (a.status === "done" ? 1 : 0) - (b.status === "done" ? 1 : 0),
  );

  const open = async ({ task, mine, status }) => {
    try {
      if (status === "done") {
        writeCurrentAssessment(mine);
        go("result");
        return;
      }
      if (status === "doing") {
        writeCurrentAssessment(mine);
        go("assessment");
        return;
      }
      writeCurrentAssessment(await taskApi.start(task.id));
      go("assessment");
    } catch (error) {
      notify?.(error.message);
    }
  };

  return (
    <div className="page">
      <PageTitle
        eyebrow="ASSESSMENT TASKS"
        title="测评任务"
        desc="老师布置的任务只需完成一次，完成后可以随时回来查看报告。"
      />
      {rows.length ? (
        <>
          <p className="task-summary">
            {pending.length ? `还有 ${pending.length} 个任务待完成` : "所有任务都已完成"}
          </p>
          <div className="task-list">
            {ordered.map((row) => {
              const { task, mine, status } = row;
              const score = mine?.averageScore ?? mine?.totalScore;
              return (
                <div className={`task-row${status === "done" ? " task-done" : ""}`} key={task.id}>
                  <div>
                    <h3>{task.title}</h3>
                    <p>{task.description || "暂无任务说明"}</p>
                  </div>
                  <div className="task-detail">
                    <span>{task.questionCount || "—"} 道题</span>
                    <span>{task.estimatedDuration || "—"} 分钟</span>
                    {status === "done" && (
                      <span className="task-status done">
                        已完成{score != null ? ` · ${score} 分` : ""}
                      </span>
                    )}
                    {status === "doing" && <span className="task-status doing">进行中</span>}
                  </div>
                  <button
                    className={status === "done" ? "outline" : "primary"}
                    onClick={() => open(row)}
                  >
                    {status === "done" ? "查看报告" : status === "doing" ? "继续测评" : "开始测评"}
                    <ArrowRight size={15} />
                  </button>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="large-empty">
          <BookOpen size={30} />
          <h3>{loading ? "正在加载任务…" : "暂无可参加的测评"}</h3>
          <p>{loading ? "稍等一下" : "先加入班级，等待老师发布任务。"}</p>
        </div>
      )}
    </div>
  );
}

export function RecordsPage({ go }) {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("all");
  const classroom = useSelectedClass();
  const isCompleted = (status) => status === "completed" || status === "completed_with_scoring_failure";
  const statusLabel = (status) => status === "completed" ? "已完成" : status === "completed_with_scoring_failure" ? "已完成（部分评分失败）" : "进行中";
  useEffect(() => {
    // 测评记录按当前选中班级过滤；没有选中班级时退回全部记录。
    assessmentApi
      .list(classroom?.id)
      .then(setItems)
      .catch(() => setItems([]));
  }, [classroom?.id]);
  return (
    <div className="page">
      <PageTitle
        eyebrow="MY RECORDS"
        title="测评记录"
        desc={classroom ? `当前班级：${classroom.name} · 只显示该班级的测评记录。` : "查看你参与过的每一次对话式测评。"}
      />
      <div className="tabs">
        <button
          className={filter === "all" ? "selected" : ""}
          onClick={() => setFilter("all")}
        >
          全部
        </button>
        <button
          className={filter === "in_progress" ? "selected" : ""}
          onClick={() => setFilter("in_progress")}
        >
          进行中
        </button>
        <button
          className={filter === "completed" ? "selected" : ""}
          onClick={() => setFilter("completed")}
        >
          已完成
        </button>
      </div>
      {(filter === "all"
        ? items
        : items.filter((item) => filter === "completed" ? isCompleted(item.status) : item.status === filter)
      ).length ? (
        <div className="record-list">
          {(filter === "all"
            ? items
            : items.filter((item) => filter === "completed" ? isCompleted(item.status) : item.status === filter)
          ).map((item) => (
            <div className="record-row" key={item.id}>
              <div>
                <h3>{item.taskId ? `测评任务 #${item.taskId}` : "自主测评"}</h3>
                <p>创建于 {item.createdAt || "—"}</p>
              </div>
              <span className={`status ${item.status}`}>
                {statusLabel(item.status)}
              </span>
              <strong>
                {item.totalScore ?? "—"}
                <small> 综合评分</small>
              </strong>
              <button
                className="outline"
                onClick={() => {
                  writeCurrentAssessment(item);
                  go(isCompleted(item.status) ? "result" : "assessment");
                }}
              >
                {isCompleted(item.status) ? "查看报告" : "继续测评"}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="large-empty">
          <BookOpen size={30} />
          <h3>还没有测评记录</h3>
          <p>完成一次对话式测评后，结果会保存在这里。</p>
          <button className="primary" onClick={() => go("classes")}>
            去参加测评 <ArrowRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * 报告中心（N3）：把该班级下的报告集中展示。
 *
 * 报告按来源分两类——教师任务（有 taskId）是「测评报告」，自主练习是「训练报告」；
 * 数据全部来自后端，前端只做分类、筛选与排序。班级隔离：切班后整表刷新。
 */
export function ReportsPage({ go, notify }) {
  const classroom = useSelectedClass();
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState("all");
  const [sort, setSort] = useState("latest");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    assessmentApi
      .list(classroom?.id)
      .then((rows) => active && setItems(rows || []))
      .catch((error) => active && notify?.(error.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [classroom?.id]);

  const isDone = (status) => status === "completed" || status === "completed_with_scoring_failure";
  const reports = items
    .filter((item) => isDone(item.status))
    .map((item) => ({
      ...item,
      kind: item.taskId ? "测评报告" : "训练报告",
      score: item.averageScore ?? item.totalScore,
    }));
  const visible = reports
    .filter((row) => tab === "all" || row.kind === tab)
    .sort((a, b) =>
      sort === "score"
        ? (b.score ?? -1) - (a.score ?? -1)
        : String(b.createdAt || "").localeCompare(String(a.createdAt || "")),
    );
  const scored = reports.filter((row) => row.score != null);
  const average = scored.length
    ? Math.round((scored.reduce((sum, row) => sum + Number(row.score), 0) / scored.length) * 10) / 10
    : null;
  const latestLevel = reports.find((row) => row.abilityLevel)?.abilityLevel || "—";

  return (
    <div className="page reports-page">
      <PageTitle
        eyebrow="REPORTS"
        title="报告中心"
        desc={classroom ? `当前班级：${classroom.name} · 报告按班级隔离` : "请先在左下角选择班级"}
      />

      <section className="report-summary">
        <article>
          <FileCheck2 size={18} />
          <span>报告总数<b>{reports.length} 份</b></span>
        </article>
        <article>
          <Gauge size={18} />
          <span>平均综合分<b>{average ?? "—"} 分</b></span>
        </article>
        <article>
          <BookOpen size={18} />
          <span>最近等级<b>{latestLevel}</b></span>
        </article>
      </section>

      <div className="report-filters">
        <div className="tabs">
          {[
            ["all", "全部报告"],
            ["测评报告", "测评报告"],
            ["训练报告", "训练报告"],
          ].map(([key, label]) => (
            <button
              type="button"
              key={key}
              className={tab === key ? "selected" : ""}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="chip-group">
          <button
            type="button"
            className={sort === "latest" ? "chip active" : "chip"}
            onClick={() => setSort("latest")}
          >
            最新优先
          </button>
          <button
            type="button"
            className={sort === "score" ? "chip active" : "chip"}
            onClick={() => setSort("score")}
          >
            分数优先
          </button>
        </div>
      </div>

      {visible.length ? (
        <div className="record-list">
          {visible.map((row) => (
            <div className="record-row" key={row.id}>
              <div>
                <h3>{row.taskId ? `测评任务 #${row.taskId}` : "自主练习测评"}</h3>
                <p>
                  {row.kind} · 创建于 {String(row.createdAt || "").slice(0, 19) || "—"}
                </p>
              </div>
              <strong>
                {row.score ?? "—"}
                <small> 综合评分</small>
              </strong>
              <button
                className="outline"
                onClick={() => {
                  writeCurrentAssessment(row);
                  go("result");
                }}
              >
                查看报告
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="large-empty">
          <FileCheck2 size={30} />
          <h3>{loading ? "正在加载报告…" : "还没有报告"}</h3>
          <p>{loading ? "稍等一下" : "完成一次测评或练习后，报告会出现在这里。"}</p>
        </div>
      )}
    </div>
  );
}
