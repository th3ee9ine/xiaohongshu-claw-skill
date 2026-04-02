# xiaohongshu-claw-skill

> 小红书笔记全流程 AI 创作工具集 — 从选题到发布，一站式生成合规的图文笔记。
>
> 当前版本：**v1.0.0**（见 [VERSION](./VERSION)）

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-brightgreen)](https://clawhub.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)

---

## 功能亮点

- **全流程自动化** — 选题 → 素材采集 → 笔记生成 → 违禁词检测 → 标题优化 → 配图规划 → HTML 渲染 → 质量评分，一条命令搞定
- **246 个违禁词检测** — 覆盖 15 个违规类别（广告法 + 小红书社区规范），支持 error/warning 分级、替换建议
- **15 套标题公式** — 数字法、痛点法、地域种草、对比反转等高 CTR 公式，自动生成 + 评分
- **8 套 HTML 模板** — 美食探店、旅行日记、好物开箱、穿搭灵感、知识分享等主流笔记类型
- **AI 配图提示词** — 自动生成封面 + 正文配图 prompt，适配 eachlabs / fal / openai / zhipu 等图片服务
- **质量评分系统** — 标题质量、违禁词风险、Tag 覆盖率、内容长度等多维度评分，给出改进建议
- **零外部依赖** — 纯 Python 3.8+，无需安装任何第三方包

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/yourname/xiaohongshu-claw-skill
cd xiaohongshu-claw-skill

# 一键跑完整流水线
python3 scripts/run_pipeline.py --topic "探店咖啡厅" --template food-explore

# 仅检测违禁词
python3 scripts/check_banned_words.py --text "全网第一！顶级品质，医生推荐！"

# 仅渲染 HTML 预览
python3 scripts/render_note.py examples/sample-food.json -o build/note.html --check

# 批量质量评分
python3 scripts/analytics.py examples/ --format table
```

## 模板一览

| 模板 | 适用场景 | 主色调 |
|------|---------|--------|
| `food-explore` | 探店 / 美食 | 暖橙 |
| `travel-diary` | 旅行 / 打卡 | 天蓝 |
| `product-unbox` | 开箱 / 测评 | 浅紫 |
| `lifestyle-review` | 生活方式 | 莫兰迪 |
| `knowledge-share` | 干货 / 教程 | 深蓝 |
| `outfit-inspo` | 穿搭 / 时尚 | 粉金 |
| `minimalist-card` | 极简卡片 | 黑白 |
| `study-log` | 学习 / 成长 | 草绿 |

## 脚本列表

| 脚本 | 功能 | 用法 |
|------|------|------|
| `run_pipeline.py` | 全流程编排 | `--topic "主题" --template 模板名` |
| `collect_sources.py` | 素材采集 | `--source-file / --source-url / --source-text` |
| `title_generator.py` | 标题生成 + 评分 | `--topic "主题" --style casual --count 10` |
| `check_banned_words.py` | 违禁词检测 CLI | `--text "文本" --suggest` |
| `plan_images.py` | 图片提示词规划 | `note.json --output-dir build/images` |
| `render_note.py` | HTML 渲染 | `note.json -o note.html --check` |
| `validate_note.py` | 结构 + 违禁词校验 | `note.json --suggest` |
| `analytics.py` | 质量评分分析 | `examples/ --format table` |

## 文档

- **完整使用文档**: [SKILL.md](./SKILL.md)
- **中文快速指南**: [docs/README.zh.md](./docs/README.zh.md)
- **OpenClaw 接入**: [docs/openclaw.zh.md](./docs/openclaw.zh.md)

## 项目结构

```
xiaohongshu-claw-skill/
├── SKILL.md                    # 完整使用文档
├── VERSION                     # 版本号
├── scripts/                    # 10 个 Python 脚本
│   ├── run_pipeline.py         # 全流程入口
│   ├── collect_sources.py      # 素材采集
│   ├── note_lib.py             # 核心渲染 & 校验库
│   ├── banned_words_lib.py     # 违禁词引擎
│   ├── check_banned_words.py   # 违禁词 CLI
│   ├── title_generator.py      # 标题生成器
│   ├── image_prompt_generator.py # AI 配图提示词
│   ├── plan_images.py          # 图片规划
│   ├── render_note.py          # HTML 渲染
│   ├── validate_note.py        # 综合校验
│   └── analytics.py            # 质量评分
├── templates/                  # 8 套 HTML 模板
├── references/                 # 违禁词库 + 写作规范 + 标题公式 + 配图指南
├── examples/                   # 示例笔记 JSON
└── docs/                       # 中文文档 + OpenClaw 接入指南
```

## 贡献

欢迎通过 PR 贡献：
- 新增模板（参考 `templates/` 目录下现有模板格式）
- 扩充违禁词库（编辑 `references/banned-words.json`）
- 新增标题公式（编辑 `scripts/title_generator.py` 中的 `FORMULAS`）

## License

[MIT](LICENSE)
