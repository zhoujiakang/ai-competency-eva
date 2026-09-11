import React, { useEffect, useState } from "react";
import { ArrowRight, Bot, Clock3 } from "lucide-react";
import { PageTitle } from "../../components/common";
import { RadarChart } from "../../components/charts";
import { assessmentApi, questionApi } from "../../services/api";
import { readCurrentAssessment, removeCurrentAssessment } from "../../app/storage";
import { isImeComposing } from "../../app/ime";

// 参考方向：后端给当前题目的基础信息里带的可点选项
const optionsOf = (question) => String(question?.options || "").split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean);

export function AssessmentPage({ go, notify }) {
  const [assessment] = useState(readCurrentAssessment);
  // 本次题量：0 表示不限题量。开始测评时由后端写在测评记录里，进度条按它显示「第 x / y 题」。
  const [planned, setPlanned] = useState(() => Number(readCurrentAssessment()?.questionCount) || 0);
  const [items, setItems] = useState([]);
  const [question, setQuestion] = useState(null);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  const pushQuestion = (next) => setItems((previous) => [...previous, { kind: "question", id: `q-${next.id}`, text: next.content, answered: false }]);

  // 后端通过 SSE 告诉我们当前发生什么：题目、发言片段、某题问完、整场结束
  const handleEvent = (aiId) => (name, payload) => {
    if (name === "delta") {
      setItems((previous) => previous.map((item) => item.id === aiId ? { ...item, text: `${item.text}${payload.text || ""}` } : item));
    } else if (name === "question") {
      setQuestion(payload);
      pushQuestion(payload);
    } else if (name === "answered") {
      setItems((previous) => previous.map((item) => item.id === `q-${payload.questionId}` ? { ...item, answered: true } : item));
    }
  };

  useEffect(() => {
    if (!assessment) {
      notify("请先从班级任务开始测评");
      go("classes");
      return;
    }
    (async () => {
      try {
        const data = await assessmentApi.conversation(assessment.id);
        // 已完成的任务不允许再次进入测评：直接打开结果页（一人一次）。
        if (data.assessment?.status && data.assessment.status !== "in_progress") {
          notify("该测评已完成，正在打开结果");
          go("result");
          return;
        }
        setItems((data.messages || []).map((message) => ({
          kind: "message",
          id: `m-${message.id}`,
          from: message.senderType === "ai" ? "ai" : "student",
          text: message.content,
        })));
        setQuestion(data.question || null);
        setPlanned(Number(data.assessment?.questionCount) || 0);
        // 还没有当前题目：让后端通过对话流给出第一道
        if (!data.question) await assessmentApi.chat(assessment.id, "", handleEvent("opening"));
      } catch (error) {
        removeCurrentAssessment();
        notify(`${error.message}，请返回工作台重新开始`);
        go("dashboard");
      }
    })();
  }, []);

  const send = async () => {
    if (!text.trim() || sending || !question) return;
    const value = text.trim();
    const stamp = Date.now();
    const studentId = `student-${stamp}`;
    const aiId = `ai-${stamp}`;
    setText("");
    setSending(true);
    setItems((previous) => [...previous,
      { kind: "message", id: studentId, from: "student", text: value },
      { kind: "message", id: aiId, from: "ai", text: "" },
    ]);
    let finished = false;
    try {
      await assessmentApi.chat(assessment.id, value, (name, payload) => {
        if (name === "finished") finished = true;
        else handleEvent(aiId)(name, payload);
      });
      // 这一轮没有说话内容（例如这道题已经答完）就别留空气泡
      setItems((previous) => previous.filter((item) => !(item.id === aiId && !item.text)));
      if (finished) {
        notify?.("测评已完成，正在打开结果");
        go("result");
      }
    } catch (error) {
      setText(value);
      setItems((previous) => previous.filter((item) => item.id !== studentId && item.id !== aiId));
      notify(error.message);
    } finally {
      setSending(false);
    }
  };

  // 中途退出不结束测评：记录保持 in_progress，之后从「测评任务」或「测评记录」点「继续测评」回来。
  // 只有把题目答完（或达到任务题量）由 Agent 自动收尾，才会真正置为已完成。
  const leaveAssessment = () => {
    notify?.("已保存进度，可以随时回来继续");
    go("dashboard");
  };

  const currentOptions = optionsOf(question);
  // 进度条：已出题数 ÷ 本次题量。不限题量（planned = 0）时只显示已出题数。
  const askedCount = items.filter((item) => item.kind === "question").length;
  const progressPercent = planned > 0 ? Math.min(100, Math.round((askedCount / planned) * 100)) : 0;
  const progressText = planned > 0
    ? `第 ${Math.min(Math.max(askedCount, 1), planned)} / ${planned} 题`
    : `已出 ${askedCount} 题 · 不限题量`;
  return (
    <div className="assessment-page">
      <div className="assessment-head">
        <button className="back-link" onClick={leaveAssessment}>← 退出（可继续）</button>
        <div className="assessment-progress">
          <strong>统一对话测评</strong>
          <div className="progress-track" role="progressbar" aria-valuenow={progressPercent} aria-valuemin={0} aria-valuemax={100}>
            <i style={{ width: `${progressPercent}%` }} />
          </div>
          <small>{progressText}</small>
        </div>
        <div className="time-left"><Clock3 size={16} /> DeepSeek Agent<button className="text-btn" onClick={leaveAssessment}>退出，稍后继续</button></div>
      </div>
      <div className="conversation">
        <div className="conversation-title"><span className="ai-symbol"><Bot size={19} /></span><div><strong>AI 测评官</strong><small>DeepSeek · 全程统一对话</small></div></div>
        {items.map((item) => <div className={`message ${item.kind === "question" ? `ai question-prompt${item.answered ? " question-answered" : ""}` : item.from}`} key={item.id}><div className="bubble">{item.text || (sending && item.from === "ai" ? "正在思考…" : "")}</div><small>{item.kind === "question" ? (item.answered ? "AI 测评官 · 本题已答完" : "AI 测评官 · 题目") : item.from === "ai" ? "AI 测评官" : "你"}</small></div>)}
        {sending && <div className="thinking"><span /><span /><span /> DeepSeek 正在思考</div>}
      </div>
      <div className="composer">
        {currentOptions.length > 0 && <div className="composer-options"><div className="composer-options-label">参考选项 · 可点击填入，也可以自行组织语言</div><div className="composer-option-list">{currentOptions.map((option) => <button key={option} type="button" onClick={() => setText(option)}>{option}</button>)}</div></div>}
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (isImeComposing(event)) return;
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              send();
            }
          }}
          placeholder={question ? "输入你的回答、理由或补充观点…" : "正在准备题目…"}
        />
        <div className="composer-foot"><span>{text.length} 字 · 开放式回答</span><button className="primary" disabled={!text.trim() || sending || !question} onClick={send}>{sending ? "发送中…" : "发送"} <ArrowRight size={16} /></button></div>
      </div>
    </div>
  );
}

export function ResultPage({ go }) {
  const [data, setData] = useState(null);
  const [taxonomy, setTaxonomy] = useState([]);
  const assessment = readCurrentAssessment();
  useEffect(() => {
    if (assessment) assessmentApi.result(assessment.id).then(setData).catch(() => {});
    questionApi.taxonomy().then(setTaxonomy).catch(() => setTaxonomy([]));
  }, []);

  // 六维雷达图：轴取固定词表（6 个维度），分数取本次测评的维度分；
  // 本次没考到的维度按 0 分画并标注出来，避免被误读成「能力为 0」。
  const axes = taxonomy.length
    ? taxonomy.map((group) => group.dimension)
    : (data?.dimensions || []).map((row) => row.dimension);
  const scoreMap = new Map((data?.dimensions || []).map((row) => [row.dimension, Number(row.score)]));
  const values = axes.map((name) => (scoreMap.has(name) ? scoreMap.get(name) : 0));
  const missing = axes.filter((name) => !scoreMap.has(name));
  const latest = data?.assessment;
  const average = latest?.averageScore ?? latest?.totalScore;
  const finished = latest?.status === "completed" || latest?.status === "completed_with_scoring_failure";

  return (
    <div className="page result-page">
      <PageTitle
        eyebrow="ASSESSMENT RESULT"
        title="测评结果"
        desc="结果来自后端 DeepSeek Agent 评分。"
        action={<button className="outline" onClick={() => go("records")}>返回测评记录</button>}
      />
      <section className="score-card">
        <div>
          <span className="eyebrow">OVERALL SCORE</span>
          <div className="score-dash">{average ?? "—"}</div>
          <p>{finished ? "测评已完成" : "测评结果处理中"} · 综合分（六维分平均）</p>
        </div>
        <div className="score-status">
          <span>{data?.hasScoringFailure ? "部分题目评分失败" : `${data?.answers?.length || 0} 道题结果`}</span>
        </div>
      </section>

      <div className="result-grid">
        <section className="panel">
          <h3>六维能力雷达图</h3>
          {axes.length ? (
            <>
              <RadarChart axes={axes} values={values} missing={missing} size={280} emptyText="本次没有可展示的维度分" />
              {missing.length > 0 && (
                <p className="chart-note">灰色标注的维度本次未考察，已按 0 分展示，不代表能力为 0。</p>
              )}
            </>
          ) : (
            <p className="chart-empty">正在加载维度…</p>
          )}
        </section>
        <section className="panel result-advice">
          <h3>学习建议</h3>
          <p>{data?.advice || "本次测评暂未生成学习建议。"}</p>
        </section>
      </div>

      <section className="panel result-breakdown">
        <h3>逐题结果</h3>
        {data?.questions?.map((q) => {
          const answer = data.answers?.find((item) => item.assessmentQuestionId === q.id);
          return (
            <div className="answer-row" key={q.id}>
              <strong>{q.sequenceNo}. {q.contentSnapshot}</strong>
              <span>{answer?.resultStatus || "未评分"} · {answer?.score ?? "—"} 分</span>
              <small>{answer?.scoringReason || "暂无评分说明"}</small>
            </div>
          );
        })}
      </section>
    </div>
  );
}
