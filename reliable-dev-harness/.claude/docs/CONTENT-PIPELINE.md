# Content Pipeline — 口播视频生产流程说明书

> 本文档描述 Reliable Dev Harness 内容生产领域的标准工作流。
> 配合 `HARNESS-ARCHITECTURE.md` 和 `CLAUDE.md` 阅读。

## 概览

内容生产流水线将口播文稿（Markdown）转化为带配音、动画、字幕的短视频。整个流程分为 4 个 Skill，每个 Skill 有 Hard Gate（确定性验证）和 Creative Gate（人类判断点）双重保证。

```
口播稿 ──→ script-writer ──→ visual-designer ──→ tts-engine ──→ video-compositor ──→ 最终视频
               G0+G1              G2+G3              G4a               G4b
            [H+CG]            [H+CG]            [H+CG]           [H+CG]
```

H = Hard Gate (exit-check.py)
CG = Creative Gate (人类确认)

## Skill 1: script-writer — 口播文稿解析与场景拆分

- **输入**: Markdown 口播文稿 或 主题描述
- **输出**: `scenes.json` + `state/L2-spec.md`
- **Hard Gate**: scenes.json 结构验证（有效 JSON，2-15 个场景，必有字段）
- **Creative Gate**: 平台选择 (9:16/16:9/4:5) + Mood + 场景拆分确认

### scenes.json 结构

```json
{
  "scenes": [
    {
      "id": "scene-01",
      "text": "口播文本内容",
      "estimatedDuration": 8,
      "visualBeats": [
        {"timeMs": 0, "type": "hook", "description": "问号符号动画"}
      ]
    }
  ]
}
```

## Skill 2: visual-designer — 视觉设计与HTML幻灯片编排

- **输入**: scenes.json + L2-spec + L3-design
- **输出**: `slides-preview.html` + 图片资产
- **Hard Gate**: HTML 有效、包含 data-beat-at 和平台 CSS、图片存在
- **Creative Gate**: 3 Style Previews 选择 + 图片确认 + 最终 HTML 预览

### 与 frontend-slides 的关系

```
visual-designer (编排器)          frontend-slides (执行器)
├── 场景→幻灯片数据转换            ├── Mood Selection 流程
├── 图片策略与管理                  ├── 3 Style Previews 生成
├── 平台覆盖 CSS 注入              ├── HTML 幻灯片渲染
├── data-beat-at 属性注入          └── 视觉设计质量保证
└── 字幕区/动画预设注入
```

## Skill 3: tts-engine — 语音合成与字幕生成

- **输入**: scenes.json (text 字段) + TTS 预设
- **输出**: `audio/` 目录 (每个场景一个 .mp3) + `subtitles.json`
- **Hard Gate**: 音频文件完整、字幕格式有效、时长偏差 ±30%
- **Creative Gate**: TTS 风格选择 (标记为 configurable skip)

### TTS 预设表

| Preset | 风格 | 音色 | 语速 |
|--------|------|------|------|
| 专业科普-女 | 清晰正式 | YunyangNeural | +0% |
| 专业科普-男 | 沉稳深度 | YunhaoNeural | -5% |
| 轻松闲聊-女 | 亲切活人感 | XiaoshuangNeural | +5% |
| 轻松闲聊-男 | 随和自然 | YunxiNeural | +0% |
| 激情解说-男 | 高能量快节奏 | YunzeNeural | +10% |
| 温柔讲述-女 | 柔和缓慢 | XiaohanNeural | -10% |

## Skill 4: video-compositor — 视频合成与输出

- **输入**: slides-preview.html + audio/ + subtitles.json + scenes.json
- **输出**: `final-video.mp4`
- **Hard Gate**: base-video 存在、分辨率匹配、fps ≥ 24、时长偏差 ±5%
- **Creative Gate**: 最终视频确认

### Remotion 渲染流程

```
slides-preview.html → Remotion Video 组件 → base-video.mp4
                                              ↓
base-video.mp4 + audio/ → ffmpeg 合成 → final-video.mp4
```

## 状态文件流转

| 阶段 | 写入 | 读取 |
|------|------|------|
| script-writer | L2-spec.md, scenes.json | L1-summary.md |
| visual-designer | L3-design.md, slides-preview.html | L2-spec.md, scenes.json |
| tts-engine | L5-media.md, audio/, subtitles.json | L2-spec.md, L3-design.md, scenes.json |
| video-compositor | L5-media.md (video section) | L2-spec.md, L5-media.md |

## 异常处理

- **Hard Gate 失败**: 退回当前 Skill 修复，不能进入下一个 Skill
- **Creative Gate 不满意**: 退回当前 Skill 重做（不是修改上游 Skill）
- **音频时长超偏差**: 需要回到 script-writer 重新评估场景拆分
- **视频渲染失败**: 检查 Remotion 项目模板配置和 slides-preview.html 有效性

## 迁移来源

本流水线从 `self-media-video` 技能（单体 G0-G4）拆分而来。原有资产分布：

| self-media-video 资产 | 目标位置 |
|----------------------|---------|
| G0-G1 逻辑 | content/script-writer/SKILL.md |
| G2 逻辑 | content/visual-designer/SKILL.md |
| G3 HTML 生成 | 委托给 frontend-slides 技能 |
| G4a TTS+字幕 | content/tts-engine/SKILL.md |
| G4b Remotion 渲染 | content/video-compositor/SKILL.md |
| templates/ | content/visual-designer/templates/ |
| project-template/ | content/video-compositor/project-template/ |
| scripts/parse-script.ts | content/script-writer/scripts/ |
| scripts/tts-*.ts | content/tts-engine/scripts/ |
| scripts/render-*.ts | content/video-compositor/scripts/ |