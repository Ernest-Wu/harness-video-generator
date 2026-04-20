---
skill: script-writer
type: scene-count
---

Scene 数量经常超过 15 个的上限，导致 video-compositor 处理时间太长。建议在 exit-check 中增加更严格的 scene 数量预警（比如 12 个就报 warning）。
