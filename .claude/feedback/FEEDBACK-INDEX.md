# Feedback Index

Steering Loop 的物理入口。所有对 harness 规则、skill 行为、state 格式的反馈都从这里开始。

## 反馈文件格式

在 `.claude/feedback/` 目录下创建 `YYYY-MM-DD_skill-type.md` 文件：

```markdown
---
skill: tts-engine
type: voice-quality
---

TTS 输出的音质不够清晰，需要调整预设。
```

**Frontmatter 字段**:
- `skill`: 反馈关联的 skill 名称（如 `tts-engine`, `dev-builder`）
- `type`: 反馈类型（如 `voice-quality`, `build-failure`, `spec-gap`）

**命名约定**: `YYYY-MM-DD_skill-type.md`，便于排序和浏览。

---

## 毕业阈值

当同一 `(skill, type)` 出现次数达到阈值时，该反馈"毕业"，可进入提案阶段：

| Domain | Threshold | 说明 |
|--------|-----------|------|
| dev | ≥ 3 | 工程类反馈收敛快 |
| pm | ≥ 2 | 决策类反馈影响大 |
| content | ≥ 5 | 主观偏好需要更多样本 |

毕业不意味着自动写入规则。EVOLUTION-RUNNER 会生成提案 diff，**必须人工确认**后才能应用到 SKILL.md 或 exit-check.py。

---

## 索引

### Unprocessed
| Date | ID | Skill | Type | Trigger | Count |
|------|-----|-------|------|---------|-------|

### Graduated (pending review)

### Applied

### Rejected

---

## 使用 feedback-analyzer

```bash
cd /path/to/project
python3 .claude/hooks/feedback-analyzer.py
```

输出示例：
```
═══ Feedback Analysis ═══

Scanned: 12 feedback file(s)

🎓 Graduated (ready for proposal):
  tts-engine / voice-quality = 5 (content threshold: 5)
  dev-builder / build-failure = 3 (dev threshold: 3)

📊 Active (below threshold):
  script-writer / scene-count = 2 (content threshold: 5)
```
