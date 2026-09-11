import React from "react";
import { findGroup, pointNames } from "../app/taxonomy";

/**
 * 考察范围选择器（维度 / 考察点），三处共用：
 * 教师建题、教师发布任务、学生自主测评。
 *
 * 一级是维度，可以多选；二级是考察点，必须落在所选维度之一。
 * AI工具使用的 8 个使用场景已经并入考察点介绍，不在这里出现。
 */

export function DimensionChips({ taxonomy, dimensions, onToggle }) {
  return (
    <div className="chip-group">
      {(taxonomy || []).map((group) => (
        <button
          type="button"
          key={group.dimension}
          className={dimensions.includes(group.dimension) ? "chip active" : "chip"}
          onClick={() => onToggle(group.dimension)}
        >
          {group.dimension}
        </button>
      ))}
    </div>
  );
}

export function PointChips({ taxonomy, dimensions, points, onToggle, showHint = true }) {
  const groups = (taxonomy || []).filter((group) => dimensions.includes(group.dimension));
  if (!groups.length) {
    return showHint ? <small className="field-hint">请先选择维度</small> : null;
  }
  return (
    <div className="chip-group">
      {groups.flatMap((group) =>
        pointNames(group).map((name) => (
          <button
            type="button"
            key={name}
            className={points.includes(name) ? "chip active" : "chip"}
            onClick={() => onToggle(name)}
          >
            {name}
          </button>
        )),
      )}
    </div>
  );
}

/** 维度 + 考察点的完整选择区。 */
export function ScopeBody({ taxonomy, dimensions, points, onToggleDimension, onTogglePoint }) {
  return (
    <div className="scope-body">
      <div className="scope-section">
        <div className="scope-label">维度{`（可多选）`}</div>
        <DimensionChips taxonomy={taxonomy} dimensions={dimensions} onToggle={onToggleDimension} />
      </div>
      <div className="scope-section">
        <div className="scope-label">考察点</div>
        <PointChips
          taxonomy={taxonomy}
          dimensions={dimensions}
          points={points}
          onToggle={onTogglePoint}
        />
      </div>
    </div>
  );
}
