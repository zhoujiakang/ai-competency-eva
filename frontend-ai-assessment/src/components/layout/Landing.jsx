import React from "react";
import { ArrowRight, MessageCircle, ShieldCheck, Sparkles } from "lucide-react";
import { Feature } from "../common";

export function Landing({ choose }) {
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand">
          <span className="brand-mark">✦</span> AI 能力测评
        </div>
        <span className="muted">对话式 · 有温度 · 可追溯</span>
      </header>
      <main className="landing-main">
        <div className="eyebrow">AI COMPETENCY EVALUATION SYSTEM</div>
        <h1>
          让能力，
          <br />
          <em>在对话中发生。</em>
        </h1>
        <p className="landing-copy">
          一次测评不是一张试卷，而是一场真实的交流。
          <br />让 AI 听见你的思考，也让结果更接近真实。
        </p>
        <div className="role-actions">
          <button className="primary big" onClick={() => choose("student")}>
            进入学生端 <ArrowRight size={18} />
          </button>
          <button className="outline big" onClick={() => choose("teacher")}>
            进入教师端 <ArrowRight size={18} />
          </button>
        </div>
        <div className="landing-note">
          <span>◌</span> 每一次回答，都成为理解你的证据
        </div>
      </main>
      <section className="landing-features">
        <Feature
          num="01"
          icon={<MessageCircle />}
          title="连续对话"
          text="不再面对标准答案，AI 会根据你的回答持续追问。"
        />
        <Feature
          num="02"
          icon={<Sparkles />}
          title="理解能力"
          text="从完整的表达中，看见思考过程、判断与创造。"
        />
        <Feature
          num="03"
          icon={<ShieldCheck />}
          title="结果可信"
          text="全程保存对话依据，评分状态透明可追溯。"
        />
      </section>
    </div>
  );
}
