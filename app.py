import json
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st
from openai import OpenAI

from main import transcribe_audio, analyze_energy, analyze_segments

st.set_page_config(page_title="EM Behavioral Coach", page_icon="🎙️", layout="wide")
st.title("🎙️ EM Behavioral Interview Coach (MVP)")
st.caption("Upload a .wav answer to get delivery + content coaching.")


def _json_safe(obj):
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def _load_questions(path: str = "data/questions_em_behavioral.json"):
    p = Path(path)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except Exception:
        return []


def _extract_json_block(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("LLM model", value="gemma2:9b")
    ollama_base_url = st.text_input("Ollama URL", value="http://localhost:11434/v1")
    save_report = st.toggle("Save JSON report", value=True)

questions = _load_questions()
if questions:
    prompt_options = [f"[{q['category']}] {q['prompt']}" for q in questions]
    selected = st.selectbox("Interview Question", options=prompt_options)
    selected_question = selected.split("] ", 1)[1]
else:
    selected_question = st.text_input("Interview Question", value="Tell me about a time you managed an underperforming engineer.")

uploaded = st.file_uploader("Upload interview answer (.wav)", type=["wav"])

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(uploaded.read())
        audio_path = tmp.name

    if st.button("Analyze", type="primary"):
        with st.spinner("Running transcription + analysis..."):
            text, segments = transcribe_audio(
                audio_path,
                prompt=(
                    "Engineering Manager behavioral interview answer. "
                    "Important terms: underperformer, performance improvement plan, one-on-one, "
                    "stakeholder, scope, impact, retrospective."
                ),
            )
            energy_info = analyze_energy(audio_path)
            segment_feedback = analyze_segments(audio_path, segments)

            client = OpenAI(base_url=ollama_base_url, api_key="ollama")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert EM behavioral interview coach.
Return ONLY valid JSON with this schema:
{
  "scores": {
    "C1_decode_accuracy": 0-10,
    "C2_story_selection_quality": 0-10,
    "C3_evidence_specificity": 0-10,
    "C4_outcomes_impact": 0-10,
    "C5_communication_judgment_reflection": 0-10,
    "content_total_60": 0-60,
    "overall_100": 0-100
  },
  "top_improvements": ["...", "...", "..."],
  "rewrite_suggestions": ["...", "..."],
  "blame_or_defensive_flags": ["..."]
}
Scoring should follow Austen-style signal quality: relevance to prompt, story quality, specificity, impact, reflection.""",
                    },
                    {
                        "role": "user",
                        "content": f"Interview question: {selected_question}\n\nTranscript:\n{text}",
                    },
                ],
                temperature=0.2,
                max_tokens=900,
            )
            raw_content_feedback = response.choices[0].message.content

            parsed_feedback = None
            try:
                parsed_feedback = json.loads(raw_content_feedback)
            except Exception:
                block = _extract_json_block(raw_content_feedback)
                if block:
                    try:
                        parsed_feedback = json.loads(block)
                    except Exception:
                        parsed_feedback = None

        st.subheader("Interview Question")
        st.write(selected_question)

        st.subheader("Transcript")
        st.write(text)

        st.subheader("Delivery Scorecard")
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Energy", f"{energy_info['overall_score']}/10")
        c2.metric("Volume", energy_info["volume_label"])
        c3.metric("Pitch Variation", str(energy_info["debug_pitch_std"]))
        st.write(energy_info["monotone_warning"])

        st.subheader("Segment Feedback")
        for fb in segment_feedback:
            st.markdown(f"**{fb['time']} — {fb['energy']}**")
            st.write(f"“{fb['text']}”")
            if fb["suggestion"]:
                st.info(fb["suggestion"])

        st.subheader("Content Coaching (Text)")
        st.write(raw_content_feedback)

        st.subheader("Content Scorecard (Parsed)")
        if parsed_feedback and "scores" in parsed_feedback:
            scores = parsed_feedback["scores"]
            a, b, c = st.columns(3)
            a.metric("Content / 60", scores.get("content_total_60", "-"))
            b.metric("Overall / 100", scores.get("overall_100", "-"))
            c.metric("Decode", scores.get("C1_decode_accuracy", "-"))

            with st.expander("Detailed parsed content feedback", expanded=False):
                st.json(parsed_feedback)
        else:
            st.warning("Could not parse structured scorecard from model output. Raw text still shown above.")

        report = {
            "timestamp": datetime.now().isoformat(),
            "question": selected_question,
            "transcript": text,
            "delivery": energy_info,
            "segments": segment_feedback,
            "content_feedback_text": raw_content_feedback,
            "content_feedback_structured": parsed_feedback,
            "llm_model": model_name,
            "llm_base_url": ollama_base_url,
        }

        report_json = json.dumps(report, indent=2, default=_json_safe)
        st.download_button(
            "Download report JSON",
            data=report_json,
            file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        if save_report:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            out_path = reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            out_path.write_text(report_json)
            st.success(f"Saved report to {out_path}")
