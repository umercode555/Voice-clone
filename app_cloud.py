"""
Voicebox Lite - Cloud mode.
Sends your text + reference voice to the free, official Chatterbox Turbo
Hugging Face Space (ResembleAI/chatterbox-turbo-demo) and downloads the result.
No local model, no torch, no heavy install - just a network call.
Needs an internet connection every time you generate.
"""

import os
import re
import shutil
import datetime

import gradio as gr
from gradio_client import Client, handle_file

SPACE_ID = "ResembleAI/chatterbox-turbo-demo"
HF_TOKEN = os.environ.get("HF_TOKEN")  # set this so requests use YOUR account quota, not the anonymous pool
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _next_run_folder():
    """Find the next free numbered folder (1, 2, 3, ...) inside OUTPUT_DIR."""
    existing = [
        int(name) for name in os.listdir(OUTPUT_DIR)
        if os.path.isdir(os.path.join(OUTPUT_DIR, name)) and name.isdigit()
    ]
    next_num = max(existing, default=0) + 1
    run_dir = os.path.join(OUTPUT_DIR, str(next_num))
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def _safe_stem(name):
    stem = os.path.splitext(os.path.basename(name))[0]
    return re.sub(r"[^A-Za-z0-9_-]+", "_", stem) or "script"


def _read_script(file_path):
    """Extract text from .txt, .pdf, or .docx script files."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        return re.sub(r"[ \t]{2,}", " ", text)

    if ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _split_into_scripts(full_text):
    """Split one file's text into separate scripts.

    Prefers real blank-line paragraphs (.txt/.docx usually keep these).
    PDFs typically lose paragraph breaks during extraction - single \\n for
    both line-wraps AND paragraph boundaries, sometimes no newline at all
    at a page break. When no blank lines are found, fall back to grouping
    sentences into 4-sentence blocks (hook + list + "comment X for the
    list" + list), which matches this hook-script template.
    """
    chunks = re.split(r"\n\s*\n", full_text)
    chunks = [c.strip().replace("\n", " ") for c in chunks if c.strip()]
    avg_len = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
    # Some PDFs insert stray blank lines around individual words (font/
    # rendering artifacts) rather than real paragraph breaks - that shows up
    # as many very short "chunks". Only trust this split when chunks look
    # like real paragraphs.
    if len(chunks) > 1 and avg_len >= 60:
        return chunks

    # Fallback for PDFs with no blank lines: reflow line-wraps into spaces,
    # split into sentences (period may have zero trailing space - PDF page
    # breaks often glue "list.Next sentence" together), group by 4.
    reflowed = re.sub(r"\s*\n\s*", " ", full_text).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s*", reflowed) if s.strip()]
    scripts = []
    for i in range(0, len(sentences), 4):
        group = " ".join(sentences[i:i + 4]).strip()
        if group:
            scripts.append(group)
    return scripts

CONNECTION_STATUS = (
    "🔑 **Using your Hugging Face account** (HF_TOKEN set) - your own quota."
    if HF_TOKEN else
    "⚠️ **Using the free anonymous queue** (no HF_TOKEN set) - shared with everyone, "
    "can be slow when busy. Set the HF_TOKEN env var and restart to use your own quota."
)

print(f"Connecting to {SPACE_ID}...")
if HF_TOKEN:
    client = Client(SPACE_ID, hf_token=HF_TOKEN)
    print("Connected (authenticated with your Hugging Face account).")
else:
    client = Client(SPACE_ID)
    print("Connected anonymously. Set HF_TOKEN env var to use your own account's quota instead.")


def _call_model(text, ref_audio, temperature, seed, min_p, top_p, top_k, repetition_penalty, norm_loudness):
    return client.predict(
        text.strip(),
        handle_file(ref_audio),
        temperature,
        seed,
        min_p,
        top_p,
        int(top_k),
        repetition_penalty,
        norm_loudness,
        api_name="/generate",
    )


def generate(text, script_files, ref_audio, temperature, seed, min_p, top_p, top_k, repetition_penalty, norm_loudness, progress=gr.Progress()):
    if not ref_audio:
        raise gr.Error("Upload or record a reference voice sample.")

    # Batch mode: one or more script files uploaded.
    if script_files:
        run_dir = _next_run_folder()
        log_lines = [f"Run folder: {run_dir}", ""]
        last_audio = None

        # Flatten every file into individual scripts first - one script per
        # detected paragraph/hook, so a single doc with 30 hooks becomes 30
        # separate audio files, not one.
        scripts = []  # list of (source_stem, script_text)
        for file_path in script_files:
            stem = _safe_stem(file_path)
            try:
                full_text = _read_script(file_path)
            except Exception as exc:
                log_lines.append(f"{stem}: FAILED to read ({exc})")
                continue

            pieces = _split_into_scripts(full_text)
            if not pieces:
                log_lines.append(f"{stem}: skipped (no text found)")
                continue
            log_lines.append(f"{stem}: extracted {len(pieces)} script(s)")
            for piece in pieces:
                scripts.append((stem, piece))

        log_lines.append("")
        log_lines.append(f"Total: {len(scripts)} script(s) across {len(script_files)} file(s). Starting generation...")
        yield None, "\n".join(log_lines), gr.update()

        consecutive_failures = 0
        for i, (stem, script_text) in enumerate(progress.tqdm(scripts, desc="Generating"), start=1):
            preview = (script_text[:60] + "...") if len(script_text) > 60 else script_text
            # Show the script currently being synthesized in the text box.
            yield last_audio, "\n".join(log_lines) + f"\n\n[{i}/{len(scripts)}] Synthesizing: \"{preview}\"", script_text

            try:
                result_path = _call_model(
                    script_text, ref_audio, temperature, seed, min_p, top_p, top_k, repetition_penalty, norm_loudness
                )
            except Exception as exc:
                consecutive_failures += 1
                log_lines.append(f"[{i}/{len(scripts)}] {stem}: FAILED - {exc}")
                if consecutive_failures >= 3:
                    log_lines.append("")
                    log_lines.append(
                        f"STOPPED after {consecutive_failures} failures in a row - likely a rate limit "
                        "or quota issue on the Chatterbox space, not a bug in the app. Wait a bit and try again."
                    )
                    yield last_audio, "\n".join(log_lines), script_text
                    return
                yield last_audio, "\n".join(log_lines), script_text
                continue

            consecutive_failures = 0
            out_path = os.path.join(run_dir, f"{i}_{stem}.wav")
            shutil.copy(result_path, out_path)
            last_audio = out_path
            log_lines.append(f"[{i}/{len(scripts)}] {stem}: done -> {os.path.basename(out_path)} - \"{preview}\"")
            yield last_audio, "\n".join(log_lines), script_text

        log_lines.append("")
        log_lines.append(f"Finished: {len(scripts)} audio file(s) generated into {run_dir}")
        yield last_audio, "\n".join(log_lines), gr.update()
        return

    # Single-text mode (original behaviour).
    if not text or not text.strip():
        raise gr.Error("Type some text to speak, or upload script files instead.")

    yield None, "Synthesizing...", gr.update()
    result_path = _call_model(text, ref_audio, temperature, seed, min_p, top_p, top_k, repetition_penalty, norm_loudness)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"chatterbox_{timestamp}.wav")
    shutil.copy(result_path, out_path)
    yield out_path, f"Saved: {out_path}", gr.update()


with gr.Blocks(title="Voicebox Lite - Cloud") as demo:
    gr.Markdown(
        "# \u26a1 Voicebox Lite (Cloud mode)\n"
        f"This sends your request to the free public **Chatterbox Turbo** Space "
        f"(`{SPACE_ID}`) and downloads the result here. Requires internet. "
        "Generation happens on their GPU, so it's much faster than running locally "
        "on this Mac - but you're sharing their free queue, so busy times may be slower."
    )
    gr.Markdown(CONNECTION_STATUS)

    with gr.Row():
        with gr.Column():
            text_in = gr.Textbox(
                label="Text to synthesize (max ~300 chars)",
                lines=5,
                value="Oh, that's hilarious! Anyway, let me tell you about this.",
            )
            script_files = gr.File(
                label="Or upload multiple scripts (.txt, .pdf, .docx) - batch mode overrides the text box above",
                file_count="multiple",
                file_types=[".txt", ".pdf", ".docx"],
            )
            ref_audio = gr.Audio(
                label="Reference voice sample (upload or record)",
                sources=["upload", "microphone"],
                type="filepath",
            )
            with gr.Accordion("Advanced Options", open=False):
                seed_num = gr.Number(value=0, label="Random seed (0 for random)")
                temp = gr.Slider(0.05, 2.0, step=0.05, value=0.8, label="Temperature")
                top_p = gr.Slider(0.0, 1.0, step=0.01, value=0.95, label="Top P")
                top_k = gr.Slider(0, 1000, step=10, value=1000, label="Top K")
                repetition_penalty = gr.Slider(1.0, 2.0, step=0.05, value=1.2, label="Repetition Penalty")
                min_p = gr.Slider(0.0, 1.0, step=0.01, value=0.0, label="Min P (0 = disabled)")
                norm_loudness = gr.Checkbox(value=True, label="Normalize Loudness (-27 LUFS)")

            generate_btn = gr.Button("Generate \u26a1", variant="primary")

        with gr.Column():
            audio_out = gr.Audio(label="Result (last generated file)")
            log_out = gr.Textbox(label="Log", lines=8, interactive=False)
            gr.Markdown(f"Saved copies land in `{OUTPUT_DIR}` - batch runs go into a new numbered subfolder each time.")

    generate_btn.click(
        fn=generate,
        inputs=[text_in, script_files, ref_audio, temp, seed_num, min_p, top_p, top_k, repetition_penalty, norm_loudness],
        outputs=[audio_out, log_out, text_in],
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861, inbrowser=True)