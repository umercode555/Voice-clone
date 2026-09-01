"""
Voicebox Lite — local voice cloning UI powered by Coqui XTTS-v2.
Runs entirely on CPU. Free, unlimited, no cloud, no account.
"""

import os
import datetime

os.environ.setdefault("COQUI_TOS_AGREED", "1")  # auto-accept the model license prompt

import gradio as gr
import torch
from TTS.api import TTS

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LANGUAGES = {
    "English": "en", "Spanish": "es", "French": "fr", "German": "de",
    "Italian": "it", "Portuguese": "pt", "Polish": "pl", "Turkish": "tr",
    "Russian": "ru", "Dutch": "nl", "Czech": "cs", "Arabic": "ar",
    "Chinese": "zh-cn", "Japanese": "ja", "Hungarian": "hu",
    "Korean": "ko", "Hindi": "hi",
}

print("Loading XTTS-v2 (first run downloads ~2GB, then it's cached)...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(MODEL_NAME).to(device)
print(f"Model loaded on {device}. Ready.")


def clone_and_speak(text, reference_audio, language_label):
    if not text or not text.strip():
        raise gr.Error("Type some text to speak.")
    if reference_audio is None:
        raise gr.Error("Upload or record a reference voice sample (5-15 seconds is plenty).")

    language = LANGUAGES.get(language_label, "en")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"clone_{timestamp}.wav")

    tts.tts_to_file(
        text=text.strip(),
        speaker_wav=reference_audio,
        language=language,
        file_path=out_path,
    )
    return out_path


with gr.Blocks(title="Voicebox Lite") as demo:
    gr.Markdown(
        "# 🎙️ Voicebox Lite\n"
        "Local, free, unlimited voice cloning powered by **XTTS-v2**. "
        "Everything runs on this machine — nothing is uploaded anywhere.\n\n"
        "**CPU note:** on older hardware, generation can take anywhere from ~20s to a couple "
        "of minutes per sentence. That's expected — it's doing real neural inference with no GPU."
    )

    with gr.Row():
        with gr.Column():
            text_in = gr.Textbox(
                label="Text to speak",
                placeholder="Type what you want the cloned voice to say...",
                lines=5,
            )
            ref_audio = gr.Audio(
                label="Reference voice sample (upload a clean 5-15s clip, or record one)",
                sources=["upload", "microphone"],
                type="filepath",
            )
            lang_in = gr.Dropdown(
                label="Language",
                choices=list(LANGUAGES.keys()),
                value="English",
            )
            generate_btn = gr.Button("Generate", variant="primary")

        with gr.Column():
            audio_out = gr.Audio(label="Result", type="filepath")
            gr.Markdown(f"Saved copies also land in `{OUTPUT_DIR}`.")

    generate_btn.click(
        fn=clone_and_speak,
        inputs=[text_in, ref_audio, lang_in],
        outputs=audio_out,
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
