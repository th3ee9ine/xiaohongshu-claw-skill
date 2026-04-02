# OpenClaw 接入指南

## 注册 Skill

在 OpenClaw workspace 的 `skills/` 目录下克隆本仓库：

```bash
cd ~/.openclaw/skills
git clone https://github.com/yourname/xiaohongshu-claw-skill
```

## 依赖 Skills

本 skill 依赖以下外部 skills（可选，仅发布时需要）：
- `nanobanana-pro-fallback` — AI 图片生成
- `xiaohongshu-api` — 小红书发布接口
- `searxng` — 素材搜索

## 使用

在 OpenClaw 对话中直接说：
> 帮我写一篇关于「杭州西湖周边酒店」的小红书笔记，模板用 travel-diary

OpenClaw 会自动定位 SKILL.md 并执行完整流程。
