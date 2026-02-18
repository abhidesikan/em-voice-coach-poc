import whisper
import librosa
import numpy as np
import os
from openai import OpenAI

# Load Whisper model (small improves accuracy for interview terminology)
model = whisper.load_model("small")

def _normalize_transcript_terms(text: str) -> str:
    replacements = {
        "entrepreneur": "underperformer",
        "entropy performer": "underperformer",
        "under sponsor": "underperformer",
        "focus improvement plan": "performance improvement plan",
        "111s": "1:1s",
        "one one ones": "1:1s",
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
        out = out.replace(src.title(), dst)
    return out


def transcribe_audio(file_path, prompt=None):
    domain_prompt = prompt or (
        "Engineering Manager interview. Terms may include: underperformer, "
        "performance improvement plan, 1:1s, stakeholder, roadmap, retrospective, impact metrics."
    )
    result = model.transcribe(
        file_path,
        initial_prompt=domain_prompt,
        temperature=0,
        condition_on_previous_text=True,
    )

    text = _normalize_transcript_terms(result["text"])
    segments = result["segments"]
    for s in segments:
        if "text" in s and isinstance(s["text"], str):
            s["text"] = _normalize_transcript_terms(s["text"])

    return text, segments

def analyze_energy(file_path):
    y, sr = librosa.load(file_path, sr=None)
    
    # Normalize audio
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    
    # RMS for volume
    rms = librosa.feature.rms(y=y)[0]
    mean_rms = np.mean(rms)
    
    # Pitch extraction using YIN (reliable for speech)
    f0 = librosa.yin(y, fmin=50, fmax=400, sr=sr, frame_length=2048)
    f0 = f0[f0 > 0]  # Remove silence/noise
    
    if len(f0) > 0:
        pitch_std = np.std(f0)
        pitch_mean = np.mean(f0)
    else:
        pitch_std = 0
        pitch_mean = 120
    
    # Scoring – prioritize intonation (key to avoiding "dead" sound)
    volume_score = np.clip(mean_rms * 40, 2, 10)
    variation_score = np.clip(pitch_std / 7, 2, 10)
    overall_score = round((volume_score * 0.4 + variation_score * 0.6), 1)
    
    # Labels
    volume_label = "Quiet" if mean_rms < 0.03 else "Moderate" if mean_rms < 0.07 else "Strong"
    
    if pitch_std < 20:
        monotone_warning = "⚠️ Very flat – sounds low energy. Vary your pitch more on key moments!"
    elif pitch_std < 35:
        monotone_warning = "ℹ️ Decent variation, but add more rise/fall for emphasis."
    else:
        monotone_warning = "✅ Excellent intonation – expressive and confident!"
    
    return {
        "overall_score": float(overall_score),
        "volume_label": volume_label,
        "monotone_warning": monotone_warning,
        "debug_rms": float(round(mean_rms, 4)),
        "debug_pitch_std": float(round(pitch_std, 1)),
        "debug_pitch_mean": float(round(pitch_mean, 1)),
    }

def analyze_segments(file_path, segments):
    y, sr = librosa.load(file_path, sr=None)
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    
    segment_feedback = []
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        
        # Skip very short or empty segments
        if len(text) < 5 or (end - start) < 2.0:
            continue
        
        # Slice audio for this segment
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        segment_audio = y[start_sample:end_sample]
        
        if len(segment_audio) == 0:
            continue
        
        rms = np.mean(librosa.feature.rms(y=segment_audio)[0])
        f0 = librosa.yin(segment_audio, fmin=50, fmax=400, sr=sr, frame_length=2048)
        f0 = f0[f0 > 0]
        pitch_std = np.std(f0) if len(f0) > 0 else 0
        
        # Energy labeling & EM-specific suggestions
        if rms < 0.03 or pitch_std < 20:
            energy_label = "Low energy"
            suggestion = "⚠️ Dip here — in EM stories, this sounds hesitant on tough calls. Amp up ownership: 'I decided to...'"
        elif rms > 0.08:
            energy_label = "Strong energy"
            suggestion = "🔥 Peak moment — lean into this for leadership vibes!"
        else:
            energy_label = "Good energy"
            suggestion = ""
        
        segment_feedback.append({
            "time": f"{start:.1f}s–{end:.1f}s",
            "text": text,
            "energy": energy_label,
            "suggestion": suggestion
        })
    
    return segment_feedback

if __name__ == "__main__":
    audio_file = "test_recording.wav"
    
    if not os.path.exists(audio_file):
        print(f"Record {audio_file} first using QuickTime → File → New Audio Recording")
    else:
        # Transcription & analysis
        text, segments = transcribe_audio(audio_file)
        energy_info = analyze_energy(audio_file)
        
        print("\nTranscript:")
        print(text)
        
        print("\n" + "="*60)
        print("DELIVERY COACHING (Voice Energy & Intonation)")
        print("="*60)
        print(f"Overall Energy Score: {energy_info['overall_score']}/10")
        print(f"Volume: {energy_info['volume_label']}")
        print(f"Intonation: {energy_info['monotone_warning']}")
        print(f"(Debug: RMS={energy_info['debug_rms']}, Pitch variation={energy_info['debug_pitch_std']})")
        
        print("\n" + "="*60)
        print("SEGMENT-BY-SEGMENT DELIVERY FEEDBACK")
        print("="*60)
        segment_feedback = analyze_segments(audio_file, segments)
        for fb in segment_feedback:
            print(f"{fb['time']}: {fb['energy']}")
            print(f"   \"{fb['text']}\"")
            if fb['suggestion']:
                print(f"   {fb['suggestion']}")
            print()  # Blank line between segments
        
        # Content coaching via local Ollama
        print("\n" + "="*60)
        print("CONTENT COACHING (Behavioral Answer Analysis)")
        print("="*60)
        
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # Dummy key – not used by Ollama
        )
        
        response = client.chat.completions.create(
            model="gemma2:9b",  # Or "llama3.2:3b" for faster responses
            messages=[
                {"role": "system", "content": """You are an expert Engineering Manager interview coach. 
Analyze this behavioral answer transcript for:
- STAR structure (Situation, Task, Action, Result) — rate each part 1-10 and explain gaps.
- Leadership & ownership — did they own outcomes, show authority with empathy?
- Impact quantification — any metrics/numbers? Suggest additions.
- Defensiveness/blame — flag if present, suggest positive reframes.
- Overall strength — score 1-10 and top 2–3 improvements.
Be specific, actionable, and encouraging."""},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        print(response.choices[0].message.content)