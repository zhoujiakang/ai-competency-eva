import React, { useEffect, useState } from "react";
import { Compass } from "lucide-react";
import { classApi, questionApi } from "../services/api";
import { readSelectedClass } from "../app/storage";
import { pointDescription, pointName } from "../app/taxonomy";
import {
  AbilityCompare,
  PointDetail,
  RadarChart,
  SkillTree,
  TrendChart,
} from "./charts";

/**
 * 当前班级：跟随侧边栏的选择，`selected-class-changed` 事件触发时自动更新。
 */
export function useSelectedClass() {
  const [classroom, setClassroom] = useState(readSelectedClass);
  useEffect(() => {
    const onChange = (event) => setClassroom(event.detail || null);
    window.addEventListener("selected-class-changed", onChange);
    return () => window.removeEventListener("selected-class-changed", onChange);
  }, []);
  return classroom;
}

/**
 * 能力数据：四张展示组件（F7–F10）与「AI 能力标准」页共用同一个数据源。
 *
 * 数据源是 `GET /api/classes/{classId}/my-ability`，切班级（classroom.id 变化）
 * 就整体重新拉取，四张图同步刷新为该班级的数据，不缓存其他班级的分数。
 */
export function useAbilityData(classroom, notify) {
  const [taxonomy, setTaxonomy] = useState([]);
  const [ability, setAbility] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    questionApi.taxonomy().then(setTaxonomy).catch(() => setTaxonomy([]));
  }, []);

  useEffect(() => {
    if (!classroom?.id) {
      setAbility(null);
      return undefined;
    }
    let active = true;
    setLoading(true);
    classApi
      .myAbility(classroom.id)
      .then((data) => active && setAbility(data))
      .catch((error) => {
        if (!active) return;
        setAbility(null);
        notify?.(error.message);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [classroom?.id]);

  const axes = taxonomy.map((group) => group.dimension);
  const scores = new Map(
    (ability?.dimensions || []).map((row) => [row.dimension, Number(row.score)]),
  );
  return {
    taxonomy,
    ability,
    loading,
    axes,
    values: axes.map((name) => (scores.has(name) ? scores.get(name) : 0)),
    missing: axes.filter((name) => !scores.has(name)),
    scoreMap: scores,
  };
}

/** 学生工作台的能力概览：综合分 + 等级 + 雷达图 + 技能树 + 趋势 + 与上一次对比。 */
export function AbilityOverview({ classroom, notify }) {
  const { taxonomy, ability, loading, axes, values, missing } = useAbilityData(classroom, notify);
  const [picked, setPicked] = useState(null);

  if (!classroom?.id) {
    return (
      <section className="panel ability-overview">
        <div className="panel-head">
          <h3>我的能力画像</h3>
        </div>
        <p className="chart-empty">请先在左下角选择班级，能力数据按班级隔离。</p>
      </section>
    );
  }

  const latest = ability?.latest;
  const hasAssessment = Boolean(ability?.hasAssessment);
  const previousValues = axes.map((name) => {
    const row = (ability?.previous?.dimensions || []).find((item) => item.dimension === name);
    return row ? Number(row.score) : 0;
  });

  return (
    <section className="ability-overview">
      <div className="panel-head">
        <div>
          <div className="eyebrow">MY ABILITY · {classroom.name}</div>
          <h3>我的能力画像</h3>
        </div>
        <span className="muted small">{loading ? "加载中…" : "数据来自该班级最新一次测评"}</span>
      </div>

      <div className="ability-hero">
        <div className="ability-score">
          <span className="eyebrow">OVERALL</span>
          <strong>
            {hasAssessment && latest.averageScore != null
              ? Math.round(latest.averageScore)
              : "—"}
          </strong>
          <small>综合分（六维分平均）</small>
        </div>
        <div className="ability-level">
          <span className={`level-badge level-${latest?.level || "L0"}`}>{latest?.level || "L0"}</span>
          <div>
            <strong>{latest?.levelName || "等待启程"}</strong>
            <small>
              {hasAssessment
                ? `完成于 ${String(latest.completedAt || "").slice(0, 10) || "—"}`
                : "本班还没有测评记录，完成首次测评后生成"}
            </small>
          </div>
        </div>
      </div>

      <div className="ability-grid">
        <article className="panel chart-panel">
          <div className="panel-head"><h3>六维雷达图</h3></div>
          <RadarChart
            axes={axes}
            values={hasAssessment ? values : null}
            missing={hasAssessment ? missing : []}
            emptyText={hasAssessment ? undefined : "完成首次测评后生成"}
          />
          {hasAssessment && missing.length > 0 && (
            <p className="chart-note">灰色标注的维度本次未考察，已按 0 分展示，不代表能力为 0。</p>
          )}
        </article>

        <article className="panel chart-panel">
          <div className="panel-head"><h3>与上一次测评对比</h3></div>
          {hasAssessment ? (
            <>
              <RadarChart
                axes={axes}
                values={values}
                compareValues={ability?.previous ? previousValues : null}
                size={260}
              />
              <AbilityCompare current={ability?.latest && { ...ability.latest, dimensions: ability.dimensions }} previous={ability?.previous} />
            </>
          ) : (
            <p className="chart-empty">完成首次测评后生成</p>
          )}
        </article>

        <article className="panel chart-panel wide">
          <div className="panel-head"><h3>成长趋势</h3></div>
          <TrendChart trend={ability?.trend || []} />
        </article>

        <article className="panel chart-panel wide">
          <div className="panel-head">
            <h3>技能树</h3>
            <span className="muted small">点击节点查看得分</span>
          </div>
          <SkillTree
            taxonomy={taxonomy}
            points={ability?.points || []}
            onSelect={setPicked}
          />
          {picked && <PointDetail point={picked} key={`${picked.name}-${picked.score}`} />}
        </article>
      </div>
    </section>
  );
}

/** 「AI 能力标准」页：6 维度 × 20 考察点 + 介绍 + 本次得分。 */
export function AbilityStandards({ classroom, notify }) {
  const { taxonomy, ability, loading } = useAbilityData(classroom, notify);
  const [openDimension, setOpenDimension] = useState(null);
  const scores = new Map(
    (ability?.points || []).map((row) => [row.assessmentPoint, Number(row.score)]),
  );

  return (
    <div className="page standards-page">
      <div className="page-title">
        <div>
          <div className="eyebrow">AI COMPETENCY STANDARD</div>
          <h1>AI 能力标准</h1>
          <p>
            六个维度共同描述一个人与 AI 协作的完整能力。每个维度下是可考察的具体考察点，
            右侧是你在该班级最近一次测评中的得分，未考察的显示「—」。
            AI工具使用维度的 8 个使用场景已经并入考察点介绍，不再单独计分。
          </p>
        </div>
      </div>
      {loading && !taxonomy.length && <p className="chart-empty">正在加载能力标准…</p>}
      <div className="standards-grid">
        {taxonomy.map((group) => {
          const points = group.points || [];
          const open = openDimension === null ? true : openDimension === group.dimension;
          return (
            <section className="panel standard-card" key={group.dimension}>
              <button
                type="button"
                className="standard-head"
                onClick={() => setOpenDimension(open ? group.dimension : null)}
              >
                <span className="standard-icon"><Compass size={16} /></span>
                <div>
                  <h3>{group.dimension}</h3>
                  <p>{group.description || "暂无维度介绍"}</p>
                </div>
                <span className="muted small">{points.length} 个考察点</span>
              </button>
              {open && (
                <ul className="standard-points">
                  {points.map((point) => {
                    const name = pointName(point);
                    const description = pointDescription(point);
                    const score = scores.get(name);
                    return (
                      <li key={name}>
                        <div className="standard-point-head">
                          <strong>{name}</strong>
                          <span className={score == null ? "point-score none" : "point-score"}>
                            {score == null ? "—" : Math.round(score)}
                          </span>
                        </div>
                        <p>{description || "暂无介绍"}</p>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}

/** 页面入口：自带当前班级，侧边栏切班后自动刷新。 */
export function StandardsPage({ notify }) {
  const classroom = useSelectedClass();
  return <AbilityStandards classroom={classroom} notify={notify} />;
}
