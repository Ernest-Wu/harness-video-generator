# Reliable Dev Harness

A dual-track product development harness combining pedagogic-first skill design with hard-gate engineering discipline. Supports both software development and content production workflows.

## Core Idea

> Vibe Coding fails not because models are dumb, but because there is no system around the model.

This harness provides:
- **Guides (前馈控制)**: Skills that inject methodology and acceptance criteria before any work begins
- **Sensors (反馈控制)**: Deterministic hooks and exit-check scripts that physically block bad output from moving forward
- **Steering Loop (进化层)**: Feedback accumulates into proposals, but **humans must confirm** before rules change
- **Context Firewall (执行隔离)**: Every Sub-Agent task runs in a fresh instance with zero inherited context

## Quick Start

```bash
# 1. Verify harness health (both domains)
python3 .claude/check-harness.py

# 2. Route a dev request to the right Skill
python3 .claude/router.py "I want to build a writing tool"
# → dev/product-spec-builder

# 3. Route a content request to the right Skill
python3 .claude/router.py "制作口播视频" --domain content
# → content/script-writer

# 4. Validate content skill output
bash .claude/hooks/content-validator.sh script-writer
```

## Architecture

```
.claude/
├── CLAUDE.md                          # Orchestrator protocol (dual-domain routing)
├── router.py                          # Skill matcher with --domain filter
├── check-harness.py                   # Dual-track health check (dev + content)
│
├── skills/
│   ├── dev/                           # Software development domain
│   │   ├── product-spec-builder/      #   PRD → L2-spec
│   │   ├── design-brief-builder/      #   Design brief → L3-design
│   │   ├── design-maker/              #   Design mockup generation
│   │   ├── dev-planner/               #   Development planning → L4-plan
│   │   ├── dev-builder/               #   Implementation
│   │   ├── bug-fixer/                 #   Bug resolution
│   │   ├── code-review/               #   Two-stage code review
│   │   └── release-builder/           #   Release packaging
│   │
│   └── content/                        # Content production domain
│       ├── script-writer/             #   口播文稿 → scenes.json + L2-spec
│       ├── visual-designer/           #   Scene → HTML slides (via frontend-slides)
│       ├── tts-engine/                #   TTS → audio/ + subtitles.json
│       └── video-compositor/          #   Compositing → final video
│
├── hooks/                              # Sensors (检查层)
│   ├── pre-commit-check.sh            #   Dev domain
│   ├── stop-gate.sh                   #   Dev domain
│   └── content-validator.sh           #   Content domain
│
├── state/                              # Hierarchical context (L1-L5)
│   ├── L1-summary.md                  #   Project overview (shared)
│   ├── L2-spec.md                     #   Dev: Product Spec / Content: Content Spec
│   ├── L3-design.md                   #   Dev: Design Brief / Content: Visual Spec
│   ├── L4-plan.md                     #   Dev: Dev Plan / Content: Pipeline Progress
│   └── L5-media.md                   #   Content: Media Asset Manifest
│
├── feedback/                           # Steering Loop inputs
├── agents/                             # Sub-Agent role definitions
│
└── docs/
    ├── HARNESS-ARCHITECTURE.md         #   Architecture documentation (dual-track)
    ├── EVOLUTION-PROTOCOL.md           #   Steering Loop protocol
    └── CONTENT-PIPELINE.md             #   Content production flow
```

## Dual-Track System

The harness now supports two domains, each with its own skill chain and gate types:

### Dev Track (Software Development)

```
idea → product-spec-builder → design-brief-builder → design-maker
  → dev-planner → dev-builder → code-review → release-builder
  [Hard Gate: exit-check.py at each step]
```

### Content Track (Oral Video Production)

```
script/topic → script-writer → visual-designer → tts-engine → video-compositor
  [Hard Gate: exit-check.py] + [Creative Gate: human confirmation]
```

Content track uses **Dual Gates**: deterministic exit-check.py (Hard Gate) PLUS human judgment points (Creative Gate) for style, pacing, and quality decisions.

## Key Design Decisions

1. **Every Skill has an exit-check.py**
   Natural language rules are unreliable. `exit-check.py` is a physical gate.

2. **Steering Loop has a Human Gate**
   `evolution-runner` may only generate proposals. It cannot directly modify Skill files.

3. **Design Mockup > Design Brief > Product Spec** (dev track)
   Visual ambiguity kills UI quality. The mockup is the single source of truth.

4. **Hard Gate + Creative Gate** (content track)
   Deterministic checks (file exists, JSON valid) + human judgment (does this look good?). Creative Gates are not skippable by default.

5. **Sub-Agent Context Firewall**
   Each task is a fresh instance. State is passed through `.claude/state/` files only.

6. **Domain-Aware Routing**
   `router.py` supports `--domain dev|content` to restrict routing to a specific domain. When domain is ambiguous, the Orchestrator asks the user.

## Non-Negotiable Rules

- Exit Code ≠ 0 means **stop**. No exceptions.
- Code changes must pass `code-review` before commit.
- No automatic rule changes without human approval.
- UI changes must sync the design mockup.
- Creative Gates in content track are not skippable unless explicitly configured.
- Content Steering Loop threshold: ≥5 same-type feedback (vs dev ≥3).

## Credits

- **Product-Manager-Skills** (deanpeters) - Pedagogic-first skill design and standardization
- **self-media-video** - Content pipeline logic (migrated into content/ skills)