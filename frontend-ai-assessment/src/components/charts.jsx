import React, { useState } from "react";
import { pointNames } from "../app/taxonomy";

/**
 * 四个展示组件的图形部件（F7–F10）。
 *
 * 全部用 SVG / CSS 自绘，不引入图表库、不依赖图片素材；数据一律来自
 * `GET /api/classes/{classId}/my-ability`，组件里不写死任何分数。
 * 阈值只在这里出现一份，改数值即可全局生效。
 */

// 技能树掌握阈值（前端计算，后端不参与）；<LEARNING 或未考察视为未解锁。
export const MASTERY_THRESHOLD = 80;
export const LEARNING_THRESHOLD = 40;

const clamp = (value) => Math.max(0, Math.min(100, Number(value) || 0));
const percent = (value) => (value == null ? null : Math.round(Number(value)));

function radarGeometry(size, axes) {
  const count = Math.max(axes.length, 3);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 58;
  const angleOf = (index) => -Math.PI / 2 + (index * 2 * Math.PI) / count;
  const pointOf = (index, value) => {
    const angle = angleOf(index);
    const distance = (radius * clamp(value)) / 100;
    return [cx + distance * Math.cos(angle), cy + distance * Math.sin(angle)];
  };
  return { cx, cy, radius, count, angleOf, pointOf };
}

const toPolygon = (geometry, values) =>
  values.map((value, index) => geometry.pointOf(index, value).join(",")).join(" ");

/**
 * 六维雷达图。
 *
 * values 顺序必须与 axes 一致；未考察的维度按 0 分画，但会加「未考察」标记，
 * 避免被误读成能力为 0。传 compareValues 时叠加一条对比线（上一次测评）。
 */
export function RadarChart({ axes = [], values = [], compareValues = null, missing = [], size = 300, emptyText }) {
  const geometry = radarGeometry(size, axes);
  const rings = [25, 50, 75, 100];
  // values 传 null 表示「还没有测评数据」：只画 0 骨架 + 空状态文案。
  const hasData = Array.isArray(values);
  const resolved = axes.map((_, index) => {
    const value = hasData ? values[index] : 0;
    return value == null ? 0 : value;
  });
  return (
    <div className="radar-chart">
      <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label="六维能力雷达图">
        {rings.map((ring) => (
          <polygon
            key={ring}
            className="radar-ring"
            points={toPolygon(geometry, axes.map(() => ring))}
          />
        ))}
        {axes.map((axis, index) => {
          const [x, y] = geometry.pointOf(index, 100);
          const [lx, ly] = (() => {
            const angle = geometry.angleOf(index);
            const distance = geometry.radius + 30;
            return [geometry.cx + distance * Math.cos(angle), geometry.cy + distance * Math.sin(angle)];
          })();
          const anchor = lx > geometry.cx + 6 ? "start" : lx < geometry.cx - 6 ? "end" : "middle";
          const isMissing = missing.includes(axis);
          return (
            <g key={axis}>
              <line className="radar-axis" x1={geometry.cx} y1={geometry.cy} x2={x} y2={y} />
              <text className={`radar-label${isMissing ? " is-missing" : ""}`} x={lx} y={ly} textAnchor={anchor}>
                {axis.length > 7 ? `${axis.slice(0, 6)}…` : axis}
              </text>
              <text className="radar-value" x={lx} y={ly + 13} textAnchor={anchor}>
                {isMissing ? "未考察" : hasData ? percent(resolved[index]) : ""}
              </text>
            </g>
          );
        })}
        {compareValues && (
          <polygon className="radar-compare" points={toPolygon(geometry, compareValues)} />
        )}
        <polygon className="radar-area" points={toPolygon(geometry, resolved)} />
        {resolved.map((value, index) => {
          const [x, y] = geometry.pointOf(index, value);
          return <circle className="radar-dot" key={axes[index]} cx={x} cy={y} r={3.2} />;
        })}
      </svg>
      {!hasData && emptyText && <p className="chart-empty">{emptyText}</p>}
    </div>
  );
}

/**
 * 技能树：主干是 6 个维度，叶子是该维度下的考察点（20 个）。
 *
 * 节点得分就是该考察点的分——题目上的场景标签（工具使用能力：编程开发）已在
 * 后端汇总回它所属的考察点，所以这里不会多出场景节点。点亮状态由前端按阈值判断，
 * 没考察到的节点置灰。
 */
export function SkillTree({ taxonomy = [], points = [], onSelect }) {
  const scoreOf = (name) => {
    const row = points.find((item) => item.assessmentPoint === name);
    return row ? Number(row.score) : null;
  };
  const statusOf = (score) => {
    if (score == null) return "locked";
    if (score >= MASTERY_THRESHOLD) return "mastered";
    if (score >= LEARNING_THRESHOLD) return "learning";
    return "locked";
  };
  return (
    <div className="skill-tree">
      <div className="skill-legend">
        <span className="skill-chip mastered">已掌握 ≥ {MASTERY_THRESHOLD}</span>
        <span className="skill-chip learning">学习中 {LEARNING_THRESHOLD}–{MASTERY_THRESHOLD - 1}</span>
        <span className="skill-chip locked">未解锁 / 未考察</span>
      </div>
      <div className="skill-branches">
        {taxonomy.map((group) => (
          <div className="skill-branch" key={group.dimension}>
            <div className="skill-trunk">
              <strong>{group.dimension}</strong>
              <small>{pointNames(group).length} 个考察点</small>
            </div>
            <div className="skill-nodes">
              {pointNames(group).map((name) => {
                const score = scoreOf(name);
                return (
                  <button
                    type="button"
                    key={name}
                    className={`skill-node ${statusOf(score)}`}
                    onClick={() => onSelect?.({ dimension: group.dimension, name, score })}
                    title={score == null ? `${name} · 未考察` : `${name} · ${Math.round(score)} 分`}
                  >
                    <span className="skill-node-dot" />
                    <span className="skill-node-name">{name}</span>
                    <span className="skill-node-score">{score == null ? "—" : Math.round(score)}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const shortDate = (value) => {
  if (!value) return "—";
  const text = String(value);
  return text.length >= 10 ? text.slice(5, 10) : text;
};

/** 成长趋势曲线：该班级下最近 N 次测评的综合分，节点标注等级。 */
export function TrendChart({ trend = [], width = 520, height = 190 }) {
  if (!trend || trend.length < 2) {
    return <p className="chart-empty">至少完成两次测评后生成趋势</p>;
  }
  const padX = 44;
  const padY = 30;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const xOf = (index) => padX + (innerW * index) / (trend.length - 1);
  const yOf = (score) => padY + (innerH * (100 - clamp(score))) / 100;
  const path = trend.map((item, index) => `${index === 0 ? "M" : "L"}${xOf(index)},${yOf(item.averageScore)}`).join(" ");
  return (
    <div className="trend-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="成长趋势曲线">
        {[0, 25, 50, 75, 100].map((line) => (
          <g key={line}>
            <line className="trend-grid" x1={padX} y1={yOf(line)} x2={width - padX} y2={yOf(line)} />
            <text className="trend-grid-label" x={padX - 8} y={yOf(line) + 4} textAnchor="end">{line}</text>
          </g>
        ))}
        <path className="trend-line" d={path} />
        {trend.map((item, index) => (
          <g key={item.assessmentId || index}>
            <circle className="trend-dot" cx={xOf(index)} cy={yOf(item.averageScore)} r={4} />
            <text className="trend-score" x={xOf(index)} y={yOf(item.averageScore) - 11} textAnchor="middle">
              {percent(item.averageScore)}
            </text>
            <text className="trend-level" x={xOf(index)} y={yOf(item.averageScore) + 19} textAnchor="middle">
              {item.level || ""}
            </text>
            <text className="trend-date" x={xOf(index)} y={height - 8} textAnchor="middle">
              {shortDate(item.completedAt)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

/** 与上一次测评对比：每个维度的增减分 + 等级变化。 */
export function AbilityCompare({ current, previous }) {
  if (!previous) {
    return <p className="chart-empty">完成第二次测评后生成对比</p>;
  }
  const scoreOf = (rows, dimension) => {
    const row = (rows || []).find((item) => item.dimension === dimension);
    return row ? Math.round(Number(row.score)) : null;
  };
  const dimensions = (current?.dimensions || []).map((item) => item.dimension);
  const levelChanged = current?.level !== previous.level;
  return (
    <div className="ability-compare">
      <p className="compare-level">
        等级：{previous.level || "L0"}
        <span className="compare-arrow">→</span>
        <strong>{current?.level || "L0"}</strong>
        {!levelChanged && <span className="compare-keep">· 与上次持平</span>}
      </p>
      <ul className="compare-list">
        {dimensions.map((dimension) => {
          const now = scoreOf(current?.dimensions, dimension);
          const before = scoreOf(previous.dimensions, dimension);
          const delta = now != null && before != null ? now - before : null;
          return (
            <li key={dimension}>
              <span>{dimension}</span>
              <span className="compare-values">
                {before == null ? "—" : before} → {now == null ? "—" : now}
              </span>
              <strong className={delta == null ? "" : delta > 0 ? "up" : delta < 0 ? "down" : ""}>
                {delta == null ? "—" : `${delta > 0 ? "+" : ""}${delta}`}
              </strong>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** 考察点详情：点击技能树节点后展示名称、分类与本次得分。 */
export function PointDetail({ point }) {
  const [open, setOpen] = useState(true);
  if (!point || !open) return null;
  return (
    <div className="point-detail">
      <div>
        <strong>{point.name}</strong>
        <small>{point.dimension}</small>
      </div>
      <span>{point.score == null ? "本次未考察" : `${Math.round(point.score)} 分`}</span>
      <button type="button" className="text-btn" onClick={() => setOpen(false)}>收起</button>
    </div>
  );
}
