import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Clock3,
  Database,
  MessageCircle,
  Plus,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Empty, Feature, Modal, PageTitle, Stat } from "../../components/common";
import { AbilityOverview } from "../../components/AbilityOverview";
import { ScopeBody } from "../../components/PointPicker";
import { assessmentApi, classApi, questionApi, taskApi } from "../../services/api";
import { readSelectedClass, writeCurrentAssessment } from "../../app/storage";
import { findGroup, pointNames } from "../../app/taxonomy";

export function StudentDashboard({ user, go, notify }) {
  const [records, setRecords] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [selectedClass, setSelectedClass] = useState(readSelectedClass);
  useEffect(() => {
    assessmentApi.list().then(setRecords).catch(() => setRecords([]));
    const classroom = readSelectedClass();
    setSelectedClass(classroom);
    if (classroom) classApi.tasks(classroom.id).then(setTasks).catch(() => setTasks([]));
    const onClassChanged = (event) => {
      const next = event.detail || null;
      setSelectedClass(next);
      if (next) classApi.tasks(next.id).then(setTasks).catch(() => setTasks([]));
      else setTasks([]);
    };
    window.addEventListener("selected-class-changed", onClassChanged);
    return () => window.removeEventListener("selected-class-changed", onClassChanged);
  }, []);
  const classRecords = records.filter((item) => !selectedClass || item.classId === selectedClass.id);
  const completedStatuses = ["completed", "completed_with_scoring_failure"];
  const pendingTasks = tasks.filter((task) => !classRecords.some((item) => item.taskId === task.id && completedStatuses.includes(item.status)));
  const activeRecord = classRecords.find((item) => item.status === "in_progress");
  // Resume targets an unfinished practice run only; teacher tasks are opened from 测评任务.
  const practiceRecord = classRecords.find((item) => !item.taskId && item.status === "in_progress");
  const [starting, setStarting] = useState(false);
  const [taxonomy, setTaxonomy] = useState([]);
  const [picking, setPicking] = useState(false);
  const [dimensions, setDimensions] = useState([]);
  const [points, setPoints] = useState([]);
  // 题量：0 表示不限（一直出到班级题库没有没用过的题为止），与后端 questionCount 口径一致。
  const [questionCount, setQuestionCount] = useState(10);
  useEffect(() => { questionApi.taxonomy().then(setTaxonomy).catch(() => setTaxonomy([])); }, []);
  // 勾维度默认带上该维度下全部考察点；考察点还可以单独加减
  const toggleDimension = (dimension) => {
    const group = pointNames(findGroup(taxonomy, dimension));
    if (dimensions.includes(dimension)) {
      setDimensions(dimensions.filter((item) => item !== dimension));
      // 这个维度下的考察点一起取消
      setPoints(points.filter((item) => !group.includes(item)));
    } else {
      setDimensions([...dimensions, dimension]);
      setPoints([...new Set([...points, ...group])]);
    }
  };
  const togglePoint = (point) => setPoints(points.includes(point) ? points.filter((item) => item !== point) : [...points, point]);
  const clearScope = () => {
    setDimensions([]);
    setPoints([]);
  };
  const openScope = () => {
    if (!selectedClass) return go("classes");
    setPicking(true);
    return undefined;
  };
  const startPractice = async () => {
    if (starting) return;
    if (!selectedClass) return go("classes");
    setStarting(true);
    try {
      // Always a brand-new practice assessment; the backend never reuses an old one here.
      // 考察范围由学生决定，不选就是不限制（使用班级全部题目）。
      writeCurrentAssessment(
        await taskApi.startSelf(selectedClass.id, {
          dimensions,
          assessmentPoints: points,
          questionCount: Number(questionCount) || 0,
        }),
      );
      setPicking(false);
      go("assessment");
    } catch (error) {
      notify?.(error.message || "无法开始测评");
    } finally {
      setStarting(false);
    }
  };
  const resumePractice = () => {
    writeCurrentAssessment(practiceRecord);
    go("assessment");
  };
  return (
    <div className="dashboard student-home">
      <section className="hero-block">
        <div className="eyebrow">YOUR NEXT CONVERSATION</div>
        <h1>你好，{user?.nickname || user?.name || "同学"}。</h1>
        <p>准备好用一场对话，重新认识自己的能力了吗？</p>
        <div className="hero-actions">
          <button className="primary big" onClick={openScope}>
            开始测评 <ArrowRight size={18} />
          </button>
          {practiceRecord && (
            <button className="outline" onClick={resumePractice}>
             继续上次练习
            </button>
          )}
        </div>
        <p className="selected-class-hint">当前班级：{selectedClass?.name || "尚未选择，请先在左下角选择"} · 每次开始都是一场全新的练习测评</p>
        {pendingTasks.length > 0 && (
          <p className="task-entry-hint">
            老师布置的测评任务还有 {pendingTasks.length} 个待完成
            <button type="button" className="text-btn" onClick={() => go("tasks")}>
              去完成 <ArrowRight size={13} />
            </button>
          </p>
        )}
      </section>
      <section className="home-intro">
        <div>
          <span className="section-index">01 / 03</span>
          <h2>
            能力，不应该
            <br />
            <em>被标准答案定义。</em>
          </h2>
        </div>
        <p>
          我们相信，真正的能力藏在你的思考过程里。AI
          测评官会倾听你的表达，提出更有针对性的问题，让每一次回答都被认真看见。
        </p>
      </section>
      <section className="feature-grid">
        <Feature
          num="01"
          icon={<MessageCircle />}
          title="多轮对话"
          text="像真实交流一样，自然地表达你的观点。"
        />
        <Feature
          num="02"
          icon={<Sparkles />}
          title="动态追问"
          text="AI 会根据你的回答，探索更深一层的思考。"
        />
        <Feature
          num="03"
          icon={<ShieldCheck />}
          title="完整留痕"
          text="对话、依据与结果，全程透明保存。"
        />
      </section>
      <section className="status-panel">
        <div>
          <div className="eyebrow">MY JOURNEY</div>
          <h2>我的测评进程</h2>
          <p>开始一场测评后，你的进度会显示在这里。</p>
        </div>
        <div className="empty-journey">
          <Clock3 size={22} />
          <span>{activeRecord ? (activeRecord.taskId ? `${activeRecord.taskTitle || "测评任务"} 正在进行中` : "练习测评正在进行中") : "暂无进行中的测评"}</span>
          <button className="outline" onClick={() => go(activeRecord ? "records" : "classes")}>
            {activeRecord ? "前往测评记录" : "查看可参加的测评"}
          </button>
        </div>
      </section>
      <AbilityOverview classroom={selectedClass} notify={notify} />
      {picking && (
        <Modal
          title="这次想考察哪些方向？"
          description="选中维度会默认带上它下面的全部考察点，也可以只留其中几个；什么都不选就是从班级题库随机出题。题量决定这次测评大概出几道题。"
          onClose={() => (starting ? undefined : setPicking(false))}
          footer={
            <>
              <span className="modal-hint">
                {dimensions.length
                  ? `已选 ${dimensions.length} 个维度 · ${points.length} 个考察点`
                  : "未选择 · 使用班级全部题目"}
              </span>
              <button type="button" className="outline" onClick={clearScope} disabled={!dimensions.length && !points.length}>
                不限范围
              </button>
              <button type="button" className="outline" onClick={() => setPicking(false)} disabled={starting}>
                取消
              </button>
              <button type="button" className="primary" onClick={startPractice} disabled={starting}>
                {starting ? "正在准备…" : "确认开始"}
              </button>
            </>
          }
        >
          {taxonomy.length ? (
            <>
              <ScopeBody
                taxonomy={taxonomy}
                dimensions={dimensions}
                points={points}
                onToggleDimension={toggleDimension}
                onTogglePoint={togglePoint}
              />
              <div className="field scope-count">
                <span>本次题量</span>
                <div className="chip-group">
                  {[5, 10, 15, 20].map((count) => (
                    <button
                      type="button"
                      key={count}
                      className={Number(questionCount) === count ? "chip active" : "chip"}
                      onClick={() => setQuestionCount(count)}
                    >
                      {count} 题
                    </button>
                  ))}
                  <button
                    type="button"
                    className={Number(questionCount) === 0 ? "chip active" : "chip"}
                    onClick={() => setQuestionCount(0)}
                  >
                    不限题量
                  </button>
                </div>
                <small className="field-hint">
                  题目按班级题库可用数量出题；选「不限题量」会一直出到没有没用过的题为止。
                </small>
              </div>
            </>
          ) : (
            <p className="scope-empty">正在加载考察范围…</p>
          )}
        </Modal>
      )}
    </div>
  );
}

export function TeacherDashboard({ user, go }) {
  const [stats, setStats] = useState({
    classes: 0,
    questions: 0,
    tasks: 0,
    students: 0,
  });
  const [recentTasks, setRecentTasks] = useState([]);
  const [recentQuestions, setRecentQuestions] = useState([]);
  useEffect(() => {
    let active = true;
    Promise.all([classApi.managed(), questionApi.list()])
      .then(async ([classes, questions]) => {
        const taskLists = await Promise.all(
          classes.map((item) => taskApi.managed(item.id).catch(() => [])),
        );
        const members = await Promise.all(
          classes.map((item) => classApi.members(item.id).catch(() => [])),
        );
        if (active)
          setStats({
            classes: classes.length,
            questions: questions.length,
            tasks: taskLists.flat().length,
            students: members.flat().length,
          });
          setRecentTasks(taskLists.flat().slice(0, 4));
          setRecentQuestions(questions.slice(0, 4));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  return (
    <div className="dashboard">
      <PageTitle
        eyebrow="TEACHER SPACE"
        title={"你好，" + (user?.nickname || user?.name || "老师") + "。"}
        desc="从这里管理你的对话题库、班级与测评任务。"
        action={
          <button className="primary" onClick={() => go("questions")}>
            <Plus size={17} /> 创建对话题
          </button>
        }
      />
      <div className="stats-grid">
        <Stat value={stats.classes} label="我的班级" />
        <Stat value={stats.questions} label="题库题目" />
        <Stat value={stats.tasks} label="已发布任务" />
        <Stat value={stats.students} label="参与学生" />
      </div>
      <div className="two-col">
        <section className="panel">
          <div className="panel-head">
            <h3>最近发布的任务</h3>
            <button className="text-btn" onClick={() => go("tasks")}>
              查看全部 <ArrowRight size={14} />
            </button>
          </div>
          {recentTasks.length ? <div className="dashboard-list">{recentTasks.map((task) => <div className="mini-row" key={task.id}><span>{task.title}</span><small>{task.questionCount} 道题</small></div>)}</div> : <Empty icon={<BookOpen />} text="还没有发布任务" action="创建第一个测评任务" />}
        </section>
        <section className="panel">
          <div className="panel-head">
            <h3>最近创建的题目</h3>
            <button className="text-btn" onClick={() => go("questions")}>
              查看全部 <ArrowRight size={14} />
            </button>
          </div>
          {recentQuestions.length ? <div className="dashboard-list">{recentQuestions.map((question) => <div className="mini-row" key={question.id}><span>{question.title}</span><small>{question.type}</small></div>)}</div> : <Empty icon={<Database />} text="题库还是空的" action="创建对话式测评题目" />}
        </section>
      </div>
    </div>
  );
}
