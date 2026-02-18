# PRD v0.1 — EM Behavioral Interview Voice Coach

## 1) Problem
Engineering managers and aspiring EMs often have good experience but underperform in behavioral rounds due to:
- weak story structure (STAR gaps)
- low impact quantification
- defensive/blame language
- flat delivery (low energy/intonation)

## 2) Target User
- Primary: 6–15 YOE software engineers moving to EM, and current EMs interviewing
- Regions: USA + India
- Language modes:
  - English mode (default)
  - Code-mix mode (future Sarvam integration)

## 3) Product Goal
Provide actionable coaching on both:
1. **Delivery** (how answer sounds)
2. **Content** (what answer says)

Output should be specific enough to improve next attempt immediately.

## 4) MVP Scope (v0.1)
- Input: recorded answer (`.wav`)
- Transcription with timestamps
- Delivery analysis:
  - overall energy score (1–10)
  - volume label
  - intonation/monotone signal
  - segment-by-segment energy flags
- Content analysis:
  - STAR scoring (S/T/A/R)
  - leadership/ownership
  - empathy/coaching tone
  - impact quantification
  - defensiveness/blame flags
- Final coaching report:
  - overall scorecard
  - top 3 improvements
  - suggested rewrite snippets

## 5) Non-Goals (v0.1)
- Real-time coaching
- Daily communication mode (outside interview context)
- Enterprise/team features
- Full web app (CLI/local first)

## 6) Success Metrics (first 20 users)
- ≥70% users say feedback is “specific and actionable”
- ≥60% users report improved confidence in second recording
- Avg session completion rate ≥80%
- At least 1 repeat session/user within 7 days

## 7) Risks
- Transcription noise can hurt content quality
- Score calibration may feel inaccurate at first
- LLM feedback may be generic without prompt/rubric tuning

## 8) Next Version (v0.2)
- Structured JSON reports + trend tracking
- Better score calibration from sample set
- Sarvam STT/code-mix pipeline
- Optional polished-answer replay (TTS)
