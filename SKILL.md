# xiaohongshu-claw-skill

> **小红书笔记全流程 AI 创作 Skill** — 从选题到发布，一站式生成合规的图文笔记。
>
> 当前版本：**v1.0.0**

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-brightgreen)](https://clawhub.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 目录

1. [快速开始](#快速开始)
2. [完整流水线](#完整流水线)
3. [笔记 JSON 格式](#笔记-json-格式)
4. [Section 类型详解](#section-类型详解)
5. [违禁词检测](#违禁词检测)
6. [标题生成](#标题生成)
7. [质量评分](#质量评分)
8. [图片指令生成](#图片指令生成)
9. [模板系统](#模板系统)
10. [Python API 速查](#python-api-速查)
11. [脚本参考](#脚本参考)
12. [示例 JSON 说明](#示例-json-说明)
13. [文件结构](#文件结构)
14. [注意事项](#注意事项)

---

## 快速开始

```bash
# 1. 一键跑完整流水线（选题 → 写作 → 图片 → 渲染 → 合规检查）
python3 scripts/run_pipeline.py --topic "探店咖啡厅" --template food-explore

# 2. 仅检测违禁词
python3 scripts/check_banned_words.py --text "全网第一！顶级品质，医生推荐！"

# 3. 检测笔记 JSON 并给出替换建议
python3 scripts/check_banned_words.py examples/sample-food.json --suggest

# 4. 仅验证结构
python3 scripts/validate_note.py examples/sample-food.json

# 5. 生成标题建议 + 评分
python3 scripts/title_generator.py --topic "探店咖啡" --style casual --count 10 --score

# 6. 批量质量评分
python3 scripts/analytics.py examples/ --format table
```

---

## 完整流水线

```
选题关键词
    │
    ▼
collect_sources.py        # 抓取参考素材 / 搜索热词
    │
    ▼
note_lib.py               # 生成笔记 JSON（meta / sections / cover / cta）
    │
    ▼
banned_words_lib.py       # 自动违禁词扫描（嵌入 validate_note）
    │
    ▼
title_generator.py        # 生成候选标题 + CTR 评分
    │
    ▼
image_prompt_generator.py # 生成封面 & 内页图片 AI 提示词
    │
    ▼
render_note.py            # 渲染 HTML（选择模板）
    │
    ▼
validate_note.py          # 最终结构 + 违禁词双重校验
    │
    ▼
analytics.py              # 综合质量评分 + 改进建议
```

### run_pipeline.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--topic` | 笔记主题关键词（与 `--json` 二选一） | 必填 |
| `--json` | 已有笔记 JSON 文件路径（与 `--topic` 二选一） | — |
| `--template` | HTML 模板名称 | 根据 `--style` 自动选择 |
| `--style` | 写作风格 `casual/professional/cute/edgy` | `casual` |
| `--output` | 输出目录 | `./output` |
| `--no-images` | 跳过图片规划步骤 | `false` |
| `--force` | 有违禁词 ERROR 也继续运行 | `false` |
| `--strict` | 有 WARNING 也终止流程 | `false` |
| `--image-service` | 图片服务 `eachlabs/fal/openai/zhipu/generic` | `generic` |

### 风格 → 模板自动映射

| `--style` | 默认模板 |
|-----------|---------|
| `casual` | `lifestyle-review` |
| `professional` | `knowledge-share` |
| `cute` | `minimalist-card` |
| `edgy` | `outfit-inspo` |

### 输出文件

流水线运行后在 `--output` 目录生成：

| 文件 | 说明 |
|------|------|
| `note.json` | 笔记结构化数据 |
| `note.html` | HTML 预览文件 |
| `images-plan.json` | 配图提示词计划 |
| `pipeline-report.json` | 流水线报告（评分、违禁词、标题候选） |

---

## 笔记 JSON 格式

所有脚本围绕统一的 JSON 格式运作。以下是完整的字段定义。

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `template` | string | ✅ | HTML 模板名称，必须是 8 个模板之一 |
| `meta` | object | ✅ | 笔记元信息 |
| `cover` | object | — | 封面图配置 |
| `sections` | array | ✅ | 笔记正文段落数组（至少 1 个） |
| `cta` | string | — | 结尾行动号召文案（默认 `"你怎么看？评论区聊聊🙌"`） |

### meta 字段

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|---------|------|
| `title` | string | ✅ | **≤ 20 字**（超出报 error） | 笔记标题 |
| `tags` | array[string] | — | 建议 3-5 个，最多 10 个 | 话题标签 |
| `author` | string | — | 默认 `"39Claw"` | 作者名 |
| `date` | string | — | ISO 格式 `YYYY-MM-DD`，默认今天 | 发布日期 |
| `location` | string | — | — | 地点信息，如 `"上海·静安区"` |

### cover 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `url` | string | 封面图 URL（有值才会渲染） |
| `caption` | string | 封面图说明文字 |
| `prompt` | string | AI 图片生成提示词 |

### 最小可用示例

```json
{
  "template": "lifestyle-review",
  "meta": {
    "title": "今日分享｜简单生活好物"
  },
  "sections": [
    {
      "type": "hook",
      "body": ["最近发现了几个超好用的生活好物，忍不住分享给大家！"]
    },
    {
      "type": "detail",
      "title": "好物推荐",
      "body": ["第一个是……", "第二个是……"]
    }
  ]
}
```

### 完整示例

```json
{
  "template": "food-explore",
  "meta": {
    "title": "上海宝藏火锅｜人均80吃到撑🔥",
    "tags": ["#上海美食", "#火锅推荐", "#探店"],
    "author": "39Claw",
    "date": "2026-03-24",
    "location": "上海·静安区"
  },
  "cover": {
    "prompt": "Steaming hot pot, red broth, close-up, food blog style, 3:4 vertical",
    "caption": "封面"
  },
  "sections": [
    {
      "type": "hook",
      "body": ["🔥 终于找到上海性价比最高的火锅！", "人均80，量大料足～"]
    },
    {
      "type": "detail",
      "title": "🍲 汤底 & 食材",
      "body": ["番茄牛骨汤底，自然酸甜。", "肥牛、毛肚必点🥩"],
      "image": {"url": "...", "caption": "菜品特写"}
    },
    {
      "type": "pros-cons",
      "pros": ["食材新鲜", "环境干净", "服务态度好"],
      "cons": ["晚高峰需等位", "停车位较少"]
    },
    {
      "type": "tips",
      "body": ["💡 工作日有优惠套餐", "📱 大众点评预约免排队"]
    },
    {
      "type": "rating",
      "items": [
        {"label": "口味", "score": "⭐⭐⭐⭐⭐"},
        {"label": "环境", "score": "⭐⭐⭐⭐"}
      ],
      "overall": "强烈推荐！"
    }
  ],
  "cta": "你们有什么宝藏火锅推荐吗？快来评论区分享🙏"
}
```

---

## Section 类型详解

`sections` 数组中的每个元素通过 `type` 字段指定渲染方式。共支持 **8 种类型**：

### hook — 开头钩子

> 前 3 行抓住注意力，决定用户是否继续阅读。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"hook"` | ✅ | — |
| `body` | string 或 array[string] | ✅ | 钩子文案，建议 1-3 句 |

```json
{
  "type": "hook",
  "body": ["🔥 终于找到上海性价比最高的火锅！", "人均80，量大料足～"]
}
```

**校验提示**：`validate_note` 会检测是否存在 hook section，缺少时发出 warning。

---

### detail — 正文段落

> 笔记的核心内容段落，支持标题和内嵌配图。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"detail"` | ✅ | — |
| `title` | string | — | 段落小标题（渲染为红色粗体） |
| `body` | string 或 array[string] | ✅ | 段落正文 |
| `image` | object | — | 内嵌配图 `{url, caption}` |
| `image_prompt` | string | — | AI 图片生成提示词（`plan_images.py` 读取） |

```json
{
  "type": "detail",
  "title": "📍 Day1 抵达 + 西湖漫步",
  "body": ["下午到杭州，先去断桥看夕阳🌅", "晚上去湖滨步行街逛吃"],
  "image": {"url": "https://...", "caption": "断桥夕阳"}
}
```

---

### pros-cons — 优缺点对比

> 增加内容可信度，红绿双色卡片样式。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"pros-cons"` | ✅ | — |
| `pros` | array[string] | — | 优点列表（✅ 绿色） |
| `cons` | array[string] | — | 缺点列表（❌ 红色） |

```json
{
  "type": "pros-cons",
  "pros": ["食材新鲜", "环境干净"],
  "cons": ["晚高峰需等位", "停车位较少"]
}
```

---

### tips — 小贴士

> 黄色高亮卡片，适合放实用建议。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"tips"` | ✅ | — |
| `body` | string 或 array[string] | ✅ | 贴士内容 |

```json
{
  "type": "tips",
  "body": ["💡 工作日有优惠套餐", "📱 大众点评预约免排队"]
}
```

---

### rating — 综合评分

> 多维度打分 + 总评卡片。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"rating"` | ✅ | — |
| `items` | array[{label, score}] | ✅ | 评分项数组 |
| `overall` | string | — | 总评文案 |

```json
{
  "type": "rating",
  "items": [
    {"label": "口味", "score": "⭐⭐⭐⭐⭐"},
    {"label": "环境", "score": "⭐⭐⭐⭐"}
  ],
  "overall": "强烈推荐！"
}
```

---

### quote — 引用 / 金句

> 左边框引用样式，适合放名言、用户评价。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"quote"` | ✅ | — |
| `text` | string | ✅ | 引用内容 |
| `attribution` | string | — | 来源署名 |

```json
{
  "type": "quote",
  "text": "旅行的意义在于，换一种方式看世界。",
  "attribution": "— 某位旅行博主"
}
```

---

### image — 独立配图

> 单独的图片展示段落（区别于 detail 的内嵌图）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"image"` | ✅ | — |
| `url` | string | ✅ | 图片 URL（无 URL 不渲染） |
| `caption` | string | — | 图注，默认 `"配图"` |

```json
{
  "type": "image",
  "url": "https://example.com/photo.jpg",
  "caption": "店内环境实拍"
}
```

**校验提示**：全部图片（cover + section 内嵌 + 独立 image）总数 ≤ 9，超出报 error；总数为 2 时报 warning（小红书算法偏好 1 或 3-9 张）。

---

### cta-block — 行动号召卡片

> 粉底红字居中卡片，比顶层 `cta` 字段更醒目。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"cta-block"` | ✅ | — |
| `body` 或 `text` | string | ✅ | CTA 文案 |

```json
{
  "type": "cta-block",
  "body": "觉得有用就收藏吧，下次出门带着看～"
}
```

---

## 违禁词检测

内置 **246 个违禁词**，覆盖 **15 个违规类别**，基于广告法及小红书平台规范。

### CLI 用法

```bash
# 检测 JSON 笔记（结构 + 违禁词）
python3 scripts/validate_note.py note.json

# 仅违禁词检测 + 替换建议
python3 scripts/check_banned_words.py note.json --suggest

# 检测原始文本
python3 scripts/check_banned_words.py --text "全网第一，顶级品质！"

# CI 集成（JSON 输出）
python3 scripts/check_banned_words.py note.json --format json

# 使用自定义词库
python3 scripts/check_banned_words.py note.json --db path/to/custom-words.json
```

### 15 大违禁词类别

| 类别 | 严重级别 | 示例 |
|------|---------|------|
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

### 内置替换建议（部分）

| 违禁词 | 建议替换 |
|--------|---------|
| 最好 | 非常好 / 效果出色 |
| 顶级 | 高端 / 优质 / 品质出色 |
| 完美 | 很好 / 令人满意 |
| 唯一 | 独特 / 别具一格 |
| 淘宝 | 某宝 / 购物平台 |
| 微信号 | （站内私信联系） |
| 治疗 | 改善 / 帮助缓解 |
| 减肥 | 管理体重 / 健康生活 |

### 在代码中集成

```python
from banned_words_lib import BannedWordsChecker

checker = BannedWordsChecker()

# 检测纯文本
result = checker.check("全网第一！顶级品质！")
print(result.summary())

# 检测完整笔记 JSON
result = checker.check_note(note_dict)
if not result.ok:
    for hit in result.errors:
        print(hit)  # ❌ ERROR  [极限词·「第一/NO.1」]  「全网第一」→ …全网第一！顶…
```

### 自定义违禁词库

编辑 `references/banned-words.json`，添加新类别：

```json
{
  "id": "custom",
  "name": "自定义敏感词",
  "severity": "warning",
  "description": "项目特定的敏感词",
  "words": ["你的词1", "你的词2"]
}
```

---

## 标题生成

基于 `title_generator.py`，提供 **15 套高 CTR 标题公式**，涵盖 6 大类型。

### CLI 用法

```bash
# 生成 10 个标题建议
python3 scripts/title_generator.py --topic "探店咖啡" --style casual --count 10

# 附加评分
python3 scripts/title_generator.py --topic "探店咖啡" --score

# JSON 输出（适合程序读取）
python3 scripts/title_generator.py --topic "探店咖啡" --format json --score

# 指定城市
python3 scripts/title_generator.py --topic "探店咖啡" --city 上海 --count 5
```

### title_generator.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--topic` | 笔记主题 | 必填 |
| `--noun` | 具体名词（默认同 topic） | — |
| `--style` | 风格 `casual/professional/cute/edgy` | `casual` |
| `--count` | 生成数量 | `10` |
| `--city` | 城市（默认随机） | — |
| `--score` | 附加评分信息 | `false` |
| `--format` | 输出格式 `text/json` | `text` |

### 15 套标题公式

| # | 公式 ID | 模板 | CTR 预估 | 限定风格 |
|---|---------|------|---------|---------|
| 1 | `num_list` | `{n}个{adj}{noun}，让你{benefit}` | ⭐ high | 全部 |
| 2 | `num_tips` | `一定要知道的{n}个{noun}技巧` | ⭐ high | 全部 |
| 3 | `num_mistake` | `踩雷{n}次后，我发现{topic}的秘密` | ⭐ high | 全部 |
| 4 | `contrast` | `你以为{wrong}，其实{right}` | ⭐ high | 全部 |
| 5 | `hidden` | `{city}藏着一家被低估的{noun}` | · mid | 全部 |
| 6 | `regret` | `早知道{topic}有这个，我就不会{mistake}` | · mid | 全部 |
| 7 | `achieve` | `靠{method}，我{outcome}` | ⭐ high | 全部 |
| 8 | `honest` | `说实话，{topic}真的{verdict}` | · mid | 全部 |
| 9 | `question` | `为什么{topic}让人{reaction}？` | · mid | 全部 |
| 10 | `secret` | `{topic}背后没人告诉你的事` | ⭐ high | 全部 |
| 11 | `location` | `在{city}找到了心目中的{noun}` | · mid | 全部 |
| 12 | `season` | `{season}必去！{city}{noun}完整攻略` | · mid | 全部 |
| 13 | `compare` | `测评了{n}家{noun}，只有这家值得去` | ⭐ high | 全部 |
| 14 | `price` | `{price}的{topic}，意外地好用` | · mid | 全部 |
| 15 | `emoji_hook` | `✨{topic}真的绝了！{benefit}` | ⭐ high | casual/cute |
| 16 | `emoji_list` | `🔥{n}个{noun}推荐，{city}必打卡` | ⭐ high | casual/cute |

> 公式中的 `{adj}` `{benefit}` `{city}` 等占位符从内置词库随机填充。标题超过 24 字自动截断为 22 字 + `…`。

### 标题评分维度

`TitleGenerator.score(title)` 从 4 个维度评分，满分 100：

| 维度 | 分值 | 判定条件 |
|------|------|---------|
| 包含数字 | +25 | 标题中有 `\d`（如"5个""30天"） |
| 包含 emoji | +25 | 标题中有 emoji 字符 |
| 包含疑问词 | +25 | 标题中有 `？` 或 `?` |
| 长度合规 | +25 | 10 ≤ 标题长度 ≤ 20 |

---

## 质量评分

`analytics.py` 提供笔记的多维度质量评分，输出综合分数（0-100）和改进建议。

### CLI 用法

```bash
# 单个笔记评分
python3 scripts/analytics.py examples/sample-food.json

# 批量评分（目录下所有 .json）
python3 scripts/analytics.py examples/ --format table

# JSON 输出
python3 scripts/analytics.py examples/sample-food.json --format json
```

### 评分公式

综合分 = 标题分 + Tag 加分 + Section 加分 + CTA 加分 + Cover 加分 − 违禁词扣分

| 维度 | 计算方式 | 范围 |
|------|---------|------|
| 标题分（基础分） | `TitleGenerator.score()` 结果 | 0-100 |
| 违禁词 ERROR | 每个 −20 | — |
| 违禁词 WARNING | 每个 −5 | — |
| Tag 数量 | 每个 +3，最多计 5 个 | 0-15 |
| Section 数量 | 每个 +5，最多计 4 个 | 0-20 |
| 有 CTA | +10 | 0-10 |
| 有封面图 | +5 | 0-5 |

**最终分数** = max(0, min(100, 计算结果))

### 风险等级

| 等级 | 条件 | 含义 |
|------|------|------|
| ✅ `safe` | 无违禁词 ERROR 且无 WARNING | 可直接发布 |
| ⚠️ `caution` | 有 WARNING 但无 ERROR | 建议修改后发布 |
| ❌ `danger` | 有 ERROR | 必须修改后才能发布 |

### 自动改进建议

评分系统会自动生成建议，例如：

- `标题建议加入数字，提升 CTR`
- `标题偏短（<10字），建议扩展`
- `Tag 数量仅 2 个，建议增加到 5-10 个`
- `正文字数偏少，建议 200 字以上增强权重`
- `缺少 CTA（号召性用语），建议结尾引导互动`
- `缺少封面图规划，建议添加 cover 字段`

---

## 图片指令生成

`image_prompt_generator.py` 和 `plan_images.py` 自动为每个笔记生成封面 + 分节配图 AI 提示词。

### CLI 用法

```bash
# 使用 image_prompt_generator（高级，支持多服务适配）
python3 scripts/image_prompt_generator.py note.json --style food --service eachlabs --format json

# 使用 plan_images（简化版，直接写入 note JSON）
python3 scripts/plan_images.py note.json --inplace --output-dir build/images
python3 scripts/plan_images.py note.json -o images-plan.json
```

### 7 种风格预设

| 风格 key | 适用场景 | 基础 prompt | 默认比例 | 推荐模型 |
|---------|---------|------------|---------|---------|
| `food` | 美食探店 | warm lighting, bokeh, appetizing | 3:4 | Flux Dev / Imagen3 |
| `travel` | 旅行打卡 | golden hour, vibrant, cinematic, 35mm | 3:4 | Flux Pro / SDXL |
| `product` | 好物开箱 | white studio, soft shadow, commercial | 1:1 | GPT-Image-1 / Flux |
| `lifestyle` | 生活方式 | natural light, moody, cozy, aesthetic | 3:4 | Flux Dev / Imagen3 |
| `outfit` | 穿搭时尚 | full body, urban, editorial style | 3:4 | Flux Dev / eachlabs |
| `knowledge` | 知识干货 | flat design, infographic, pastel | 1:1 | DALL-E 3 / Imagen3 |
| `study` | 学习成长 | desk setup, stationery, warm light | 1:1 | Flux Dev |

> 风格自动根据模板名推断（如 `food-explore` → `food`），也可通过 `--style` 手动指定。

### 封面图规格

| 平台位置 | 尺寸 | 比例 |
|---------|------|------|
| 小红书封面 | 1080×1440 | 3:4 |
| 小红书正文 | 1080×1080 | 1:1 |
| 小红书横版 | 1440×1080 | 4:3 |

### 多服务适配

`ImagePrompt.for_service(service)` 自动转换为不同图片服务的 API 参数格式：

| 服务 | 参数格式 |
|------|---------|
| `eachlabs` | `{prompt, negative_prompt, aspect_ratio, model}` |
| `fal` | `{prompt, negative_prompt, image_size}` — image_size: `portrait_4_3` / `square` / `landscape_4_3` |
| `openai` | `{prompt, size, quality, style}` — size: `1024x1792` / `1024x1024` / `1792x1024` |
| `zhipu` | `{prompt}` — 中文理解更强，prompt 自动拼接风格描述 |
| `generic` | 原始字段（positive / negative / ratio / model_hint） |

---

## 模板系统

8 套 HTML 模板，覆盖主流笔记类型：

| 模板文件 | 适用场景 | 主色调 | 标题色 |
|---------|---------|--------|-------|
| `food-explore.html` | 探店/美食 | 暖橙 `#fff8f0` | `#e8600a` |
| `travel-diary.html` | 旅行/打卡 | 天蓝 `#f0f8ff` | — |
| `product-unbox.html` | 开箱/测评 | 浅紫 `#fdf5ff` | — |
| `lifestyle-review.html` | 生活方式 | 莫兰迪 `#fafafa` | — |
| `knowledge-share.html` | 干货/教程 | 淡绿 `#f5fff5` | — |
| `outfit-inspo.html` | 穿搭/时尚 | 粉色 `#fff0f8` | — |
| `minimalist-card.html` | 极简卡片 | 黑白 `#fafafa` | — |
| `study-log.html` | 学习/成长 | 浅蓝 `#f5faff` | — |

### 模板占位符

所有模板使用统一的占位符，由 `note_lib.render_note()` 自动替换：

| 占位符 | 来源 | 说明 |
|--------|------|------|
| `{{TITLE}}` | `meta.title` | 笔记标题 |
| `{{AUTHOR}}` | `meta.author` | 作者名 |
| `{{DATE_SHORT}}` | `meta.date` → `YYYY.MM.DD` | 日期短格式 |
| `{{LOCATION}}` | `meta.location` | 地点（有值才渲染） |
| `{{COVER_IMAGE}}` | `cover.url` | 封面图（有 URL 才渲染） |
| `{{HOOK_SECTION}}` | 第一个 `type: hook` 的 section | 钩子段落 |
| `{{BODY_SECTIONS}}` | 全部 sections | 正文段落 |
| `{{TAGS_LINE}}` | `meta.tags` | 话题标签行 |
| `{{CTA}}` | `cta` | 结尾行动号召 |

```bash
python3 scripts/render_note.py note.json --template food-explore --output note.html
```

---

## Python API 速查

所有模块均可在 Python 代码中直接 import 使用（需确保 `scripts/` 目录在 `sys.path` 中）。

### 违禁词检测

```python
from banned_words_lib import BannedWordsChecker

checker = BannedWordsChecker()

# 检测文本
result = checker.check("全网第一！顶级品质！")
print(result.summary())          # 共发现 2 个错误、0 个警告：…
print(result.ok)                 # False（有 error）

# 检测笔记 JSON
result = checker.check_note(note_dict)
for hit in result.errors:
    print(hit.word, hit.category_name, hit.context)

# 查看所有类别
for cat in checker.categories():
    print(cat["id"], cat["name"], len(cat["words"]), "词")
```

### 标题生成与评分

```python
from title_generator import TitleGenerator

gen = TitleGenerator(seed=42)  # 可选固定种子

# 生成标题
titles = gen.generate(topic="探店咖啡", style="casual", count=10, city="上海")
for t in titles:
    print(t)          # ⭐ [num_list] 5个宝藏探店咖啡，让你收获满满
    print(t.text)     # 5个宝藏探店咖啡，让你收获满满
    print(t.formula)  # num_list
    print(t.ctr)      # high

# 评分
score = gen.score("5个让你惊艳的咖啡馆✨")
print(score)
# {'title': '...', 'score': 75, 'has_number': True, 'has_emoji': True,
#  'has_question': False, 'length_ok': True, 'length': 12}
```

### AI 配图提示词

```python
from image_prompt_generator import ImagePromptGenerator

gen = ImagePromptGenerator()

# 为整篇笔记生成提示词
prompts = gen.generate_for_note(note_dict, service="eachlabs")
for p in prompts:
    print(p.purpose)        # cover / section_1 / section_2
    print(p.positive[:80])  # 正向提示词
    print(p.ratio)          # 3:4
    print(p.for_service("eachlabs"))  # API-ready 参数

# 仅生成封面
cover = gen.generate_cover_only("杭州西湖日落", style_key="travel", service="fal")
print(cover.for_service("fal"))

# 查看所有可用风格
print(gen.list_styles())  # ['food', 'travel', 'product', ...]
```

### 笔记渲染与校验

```python
from note_lib import load_json, render_note, validate_note

# 加载 + 渲染
note = load_json("examples/sample-food.json")
html = render_note(note)

# 校验（结构 + 违禁词）
result = validate_note(note, html_text=html)
if result.ok:
    print("✅ 校验通过")
else:
    for e in result.errors:
        print(f"ERROR: {e}")
    for w in result.warnings:
        print(f"WARNING: {w}")
```

### 质量评分

```python
from analytics import analyse_file
from pathlib import Path

score = analyse_file(Path("examples/sample-food.json"))
print(f"综合评分: {score.overall}/100")
print(f"风险等级: {score.risk_level}")    # safe / caution / danger
print(f"标题评分: {score.title_score}")
print(f"违禁词 ERROR: {score.banned_errors}")
print(f"违禁词 WARNING: {score.banned_warnings}")
print(f"Tag 数量: {score.tag_count}")
print(f"正文字数: {score.total_chars}")
for s in score.suggestions:
    print(f"  💡 {s}")
```

---

## 脚本参考

| 脚本 | 功能 | 主要参数 |
|------|------|---------|
| `run_pipeline.py` | 全流程编排 | `--topic --template --style --image-service` |
| `collect_sources.py` | 素材/热词采集 | `--source-file --source-url --source-text -o` |
| `note_lib.py` | 笔记 JSON 生成、渲染与校验 | Python API |
| `banned_words_lib.py` | 违禁词检测引擎 | Python API |
| `check_banned_words.py` | 违禁词 CLI | `--text --suggest --format --db` |
| `title_generator.py` | 标题生成 + 评分 CLI | `--topic --style --count --score --format` |
| `image_prompt_generator.py` | AI 配图提示词引擎 | `--style --service --format` |
| `plan_images.py` | 图片提示词规划（简化版） | `--inplace --output-dir --max-images` |
| `render_note.py` | HTML 渲染 | `--template --output --check` |
| `validate_note.py` | 结构 + 违禁词双重校验 | `--banned-only --no-banned --suggest --format` |
| `analytics.py` | 质量评分与分析 | `--format table/json` |

---

## 示例 JSON 说明

`examples/` 目录提供 3 个完整的笔记示例，可直接用于测试全流程：

| 文件 | 主题 | 模板 | 特点 |
|------|------|------|------|
| `sample-food.json` | 上海火锅探店 | `food-explore` | hook + detail + pros-cons + tips |
| `sample-product.json` | 保湿面霜开箱 | `product-unbox` | hook + detail + pros-cons + rating |
| `sample-travel.json` | 杭州 3 天 2 夜攻略 | `travel-diary` | hook + 多个 detail（Day1/Day2）+ pros-cons + tips + rating + image_prompt |

```bash
# 快速体验
python3 scripts/render_note.py examples/sample-food.json -o build/food.html --check
python3 scripts/analytics.py examples/ --format table
```

---

## 文件结构

```
xiaohongshu-claw-skill/
├── SKILL.md                        # 本文档（完整使用手册）
├── README.md                       # 项目介绍
├── VERSION                         # 版本号（纯文本，如 1.0.0）
├── LICENSE                         # MIT 许可证
├── .gitignore
├── scripts/
│   ├── run_pipeline.py             # 全流程入口
│   ├── collect_sources.py          # 素材采集
│   ├── note_lib.py                 # 核心库（渲染 + 校验）
│   ├── banned_words_lib.py         # 违禁词引擎 ★
│   ├── check_banned_words.py       # 违禁词 CLI ★
│   ├── title_generator.py          # 标题生成 + 评分 ★
│   ├── image_prompt_generator.py   # AI 配图提示词引擎 ★
│   ├── plan_images.py              # 图片规划（简化版）
│   ├── render_note.py              # HTML 渲染
│   ├── validate_note.py            # 综合校验
│   └── analytics.py                # 质量评分 ★
├── templates/                      # 8 套 HTML 模板
│   ├── food-explore.html
│   ├── travel-diary.html
│   ├── product-unbox.html
│   ├── lifestyle-review.html
│   ├── knowledge-share.html
│   ├── outfit-inspo.html
│   ├── minimalist-card.html
│   └── study-log.html
├── references/
│   ├── banned-words.json           # 违禁词库（246 词 / 15 类）★
│   ├── title-formulas.md           # 标题公式
│   ├── writing-guide.md            # 写作规范
│   └── image-prompt-guide.md       # 图片提示词指南
├── examples/
│   ├── sample-food.json
│   ├── sample-product.json
│   └── sample-travel.json
└── docs/
    ├── README.zh.md                # 中文快速指南
    └── openclaw.zh.md              # OpenClaw 接入指南
```

---

## 注意事项

- 本 Skill 仅供内容创作辅助，不保证 100% 通过平台审核，请结合实际发布效果持续优化词库
- 违禁词库来源：中国广告法 + 小红书社区规范（2025 年版），建议定期更新 `references/banned-words.json`
- 导流词（如「微信」「淘宝」）检测为 error 级别，发布前务必修改
- HTML 模板用于预览/设计参考，最终需在小红书 APP 内手动排版
- 标题严格 ≤ 20 字（含标点符号），超出会被 `validate_note` 报 error
- 图片总数 ≤ 9 张（含封面），超出会被报 error；总数为 2 张时会报 warning（算法偏好 1 或 3-9 张）
- Python 3.8+，无外部依赖，开箱即用

---

*Maintained by the OpenClaw community. Contributions welcome via PR.*
