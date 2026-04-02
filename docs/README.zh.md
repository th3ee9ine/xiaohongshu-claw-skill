# xiaohongshu-claw-skill 中文文档

> 一站式小红书笔记自动化创作工具集，从选题到发布全流程覆盖。

---

## 简介

xiaohongshu-claw-skill 是一套面向小红书内容创作者的 AI 辅助工具集，提供：

- **全流程自动化** — 一条命令完成：素材采集 → 笔记生成 → 违禁词检测 → 标题优化 → 配图规划 → HTML 渲染 → 质量评分
- **合规检测** — 内置 246 个违禁词（15 个类别），涵盖广告法 + 小红书社区规范，自动扫描并给出替换建议
- **8 套 HTML 模板** — 美食、旅行、开箱、穿搭、干货等主流笔记类型全覆盖
- **AI 配图规划** — 自动生成封面 + 正文配图提示词，适配主流图片生成服务
- **质量评分** — 多维度分析标题、内容、标签，给出改进建议和发布风险评估

## 安装依赖

只需 Python 3.8+，**无额外依赖**，开箱即用。

```bash
git clone https://github.com/yourname/xiaohongshu-claw-skill
cd xiaohongshu-claw-skill
```

---

## 快速开始

### 一键全流程

```bash
python3 scripts/run_pipeline.py --topic "探店咖啡厅" --template food-explore
```

输出文件（默认在 `./output/` 目录）：
- `note.json` — 笔记数据
- `note.html` — HTML 预览
- `images-plan.json` — 配图提示词
- `pipeline-report.json` — 流水线报告（含评分和建议）

### 仅违禁词检测

```bash
# 检测文本
python3 scripts/check_banned_words.py --text "全网第一！顶级品质，医生推荐！"

# 检测笔记 JSON + 替换建议
python3 scripts/check_banned_words.py examples/sample-food.json --suggest

# CI 集成（JSON 输出）
python3 scripts/check_banned_words.py note.json --format json
```

### 仅渲染 HTML

```bash
python3 scripts/render_note.py examples/sample-travel.json -o build/note.html --check
```

### 生成标题建议

```bash
python3 scripts/title_generator.py --topic "探店咖啡" --style casual --count 10 --score
```

### 图片规划

```bash
python3 scripts/plan_images.py examples/sample-food.json -o build/images-plan.json
```

### 质量评分

```bash
# 单个笔记
python3 scripts/analytics.py examples/sample-food.json

# 批量评分
python3 scripts/analytics.py examples/ --format table
```

---

## 笔记 JSON 格式说明

所有脚本围绕统一的 JSON 格式运作：

```json
{
  "template": "food-explore",
  "meta": {
    "title": "杭州｜巷子里的宝藏火锅店",
    "tags": ["杭州美食", "火锅", "探店", "宝藏小店"],
    "author": "39Claw",
    "date": "2025-06-10",
    "location": "杭州·西湖区"
  },
  "cover": {
    "url": "https://example.com/cover.jpg",
    "caption": "火锅封面",
    "prompt": "Appetizing hot pot photography..."
  },
  "sections": [
    {
      "type": "hook",
      "body": ["在杭州吃了三年火锅，这家店让我惊了 🔥"]
    },
    {
      "type": "detail",
      "title": "环境氛围",
      "body": ["藏在巷子里，门面不大但装修很有质感。", "暖色灯光 + 原木桌椅，拍照很出片。"],
      "image": {"url": "...", "caption": "店内环境"}
    },
    {
      "type": "pros-cons",
      "pros": ["食材新鲜", "锅底醇厚", "服务态度好"],
      "cons": ["排队时间长", "停车不方便"]
    },
    {
      "type": "tips",
      "body": ["建议工作日去，周末排队 1 小时+", "必点：鲜毛肚、手切牛肉"]
    },
    {
      "type": "rating",
      "items": [
        {"label": "口味", "score": "⭐⭐⭐⭐⭐"},
        {"label": "环境", "score": "⭐⭐⭐⭐"},
        {"label": "性价比", "score": "⭐⭐⭐⭐"}
      ],
      "overall": "强烈推荐！"
    }
  ],
  "cta": "你在杭州吃过哪家火锅最惊艳？评论区分享吧 🙌"
}
```

### Section 类型一览

| type | 用途 | 必填字段 |
|------|------|---------|
| `hook` | 开头钩子（前 3 行抓注意力） | `body` |
| `detail` | 正文段落（支持标题 + 配图） | `body`，可选 `title` / `image` |
| `pros-cons` | 优缺点对比 | `pros` / `cons`（数组） |
| `tips` | 小贴士 / 建议 | `body` |
| `rating` | 综合评分 | `items`（数组），可选 `overall` |
| `quote` | 引用 / 金句 | `text`，可选 `attribution` |
| `image` | 独立配图 | `url`，可选 `caption` |
| `cta-block` | 行动号召（卡片样式） | `body` 或 `text` |

---

## 流水线参数

### run_pipeline.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--topic` | 笔记主题（新建笔记） | 与 `--json` 二选一 |
| `--json` | 已有笔记 JSON 路径 | 与 `--topic` 二选一 |
| `--template` | HTML 模板名称 | 根据 `--style` 自动选择 |
| `--style` | 写作风格：`casual` / `professional` / `cute` / `edgy` | `casual` |
| `--output` | 输出目录 | `./output` |
| `--no-images` | 跳过图片规划 | `false` |
| `--force` | 有违禁词 ERROR 也继续 | `false` |
| `--strict` | WARNING 也终止流程 | `false` |
| `--image-service` | 图片服务：`eachlabs` / `fal` / `openai` / `zhipu` / `generic` | `generic` |

---

## 模板系统

8 套 HTML 模板，覆盖主流笔记类型：

| 模板文件 | 适用场景 | 主色调 |
|---------|---------|--------|
| `food-explore.html` | 探店 / 美食 | 暖橙 #fff8f0 |
| `travel-diary.html` | 旅行 / 打卡 | 天蓝 #f0f8ff |
| `product-unbox.html` | 开箱 / 测评 | 浅紫 #fdf5ff |
| `lifestyle-review.html` | 生活方式 | 莫兰迪 #fafafa |
| `knowledge-share.html` | 干货 / 教程 | 淡绿 #f5fff5 |
| `outfit-inspo.html` | 穿搭 / 时尚 | 粉色 #fff0f8 |
| `minimalist-card.html` | 极简卡片 | 黑白 #fafafa |
| `study-log.html` | 学习 / 成长 | 浅蓝 #f5faff |

模板使用占位符渲染：`{{TITLE}}`、`{{AUTHOR}}`、`{{DATE_SHORT}}`、`{{LOCATION}}`、`{{COVER_IMAGE}}`、`{{HOOK_SECTION}}`、`{{BODY_SECTIONS}}`、`{{TAGS_LINE}}`、`{{CTA}}`。

---

## 违禁词系统

内置 **246 个违禁词**，覆盖 **15 个违规类别**：

| 类别 | 级别 | 示例 |
|------|------|------|
| 极限词·含「级/极」 | ❌ error | 极致、顶级、宇宙级 |
| 极限词·「第一/NO.1」 | ❌ error | 全国第一、TOP1 |
| 极限词·含「首」 | ❌ error | 首个、首选、全国首家 |
| 极限词·最好/最强类 | ❌ error | 最好、最强、最佳 |
| 极限词·唯一/独家类 | ❌ error | 唯一、独一无二、独家 |
| 极限词·绝对化表述 | ❌ error | 万能、完美、天花板 |
| 夸张诱导词 | ❌ error | 抢疯了、秒杀、全民免单 |
| 权威性词语 | ❌ error | 专家推荐、质量免检 |
| 导流词·站外引流 | ❌ error | 微信号、淘宝、抖音 |
| 诱导行为词 | ⚠️ warning | 点赞、收藏、扫码 |
| 营销促销词 | ⚠️ warning | 返利、日销冠、带货 |
| 承诺保证词 | ❌ error | 包过、月入过万 |
| 玄学迷信词 | ⚠️ warning | 旺财、算命、运势 |
| 医疗健康违规词 | ❌ error | 治疗、根治、暴瘦 |
| 标题党禁用词 | ⚠️ warning | 震惊、99%的人不知道 |

### 自定义违禁词

编辑 `references/banned-words.json`，添加新类别：

```json
{
  "id": "custom",
  "name": "自定义敏感词",
  "severity": "warning",
  "description": "项目特定的敏感词",
  "words": ["词1", "词2"]
}
```

---

## 在代码中使用

### 违禁词检测

```python
from banned_words_lib import BannedWordsChecker

checker = BannedWordsChecker()
result = checker.check("全网第一！顶级品质！")
print(result.summary())

# 检测完整笔记
result = checker.check_note(note_dict)
if not result.ok:
    for hit in result.errors:
        print(hit)
```

### 标题生成

```python
from title_generator import TitleGenerator

gen = TitleGenerator()
titles = gen.generate(topic="探店咖啡", style="casual", count=10)
for t in titles:
    print(t)

# 评分
score = gen.score("5个让你惊艳的咖啡馆")
print(f"得分: {score['score']}/100")
```

### AI 配图

```python
from image_prompt_generator import ImagePromptGenerator

gen = ImagePromptGenerator()
prompts = gen.generate_for_note(note_dict, service="eachlabs")
for p in prompts:
    print(f"[{p.purpose}] {p.positive[:80]}...")
```

---

## 示例 JSON

`examples/` 目录提供 3 个完整示例：
- `sample-food.json` — 美食探店（火锅）
- `sample-product.json` — 好物开箱（护肤品）
- `sample-travel.json` — 旅行日记（杭州 3 日）

---

## 注意事项

- 本工具仅供内容创作辅助，不保证 100% 通过平台审核
- 违禁词库来源：中国广告法 + 小红书社区规范（2025 年版），建议定期更新
- 导流词（微信、淘宝等）检测为 error 级别，发布前务必修改
- HTML 模板用于预览/设计参考，最终需在小红书 APP 内手动排版

---

*Maintained by the OpenClaw community. Contributions welcome via PR.*
