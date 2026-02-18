# PROJECT_STATE.md

## Project
EM Voice Coach POC (Interview-focused)

## Current Goal
Build an interview-specific coaching tool for Engineering Manager behavioral rounds with two feedback layers:
1. Delivery (energy, intonation, monotone dips, segment-level timing)
2. Content (STAR quality, ownership, impact quantification, defensiveness)

## Scope Direction (Locked)
- Keep product specific to **interviews** for now.
- Build for both USA + India users via one product:
  - English mode (global default)
  - Code-mix mode (Sarvam-powered; later integration)

## What Exists Today
- `main.py` pipeline in place.
- Local audio transcription + delivery analysis working.
- Segment-level feedback working.
- Local content coaching path tested.

## Open Questions
- Exact MVP rubric weights for delivery/content.
- Sarvam integration order (STT first vs STT+TTS together).
- Initial question bank size and categories.

## Next 3 Actions
1. Write v0.1 PRD (1 page) for interview-only scope.
2. Define scoring rubric (dimensions + 1–10 scale mapping).
3. Plan minimal Sarvam integration path (phase-wise).

## Last Updated
2026-02-17 (America/Los_Angeles)
