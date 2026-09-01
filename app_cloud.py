"""
Voicebox Lite - Cloud mode.
Sends your text + reference voice to the free, official Chatterbox Turbo
Hugging Face Space (ResembleAI/chatterbox-turbo-demo) and downloads the result.
No local model, no torch, no heavy install - just a network call.
Needs an internet connection every time you generate.
"""

import os
import shutil
import datetime

import gradio as gr
from gradio_client import Client, handle_file

SPACE_ID = "ResembleAI/chatterbox-turbo-demo"
HF_TOKEN = os.environ.get("HF_TOKEN")  # set this so requests use YOUR account quota, not the anonymous pool
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Connecting to {SPACE_ID}...")
if HF_TOKEN:
    client = Client(SPACE_ID, hf_token=HF_TOKEN)
    print("Connected (authenticated with your Hugging Face account).")
else:
    client = Client(SPACE_ID)
    print("Connected anonymously. Set HF_TOKEN env var to use your own account's quota instead.")


def generate(text, ref_audio, temperature, seed, min_p, top_p, top_k, repetition_penalty, norm_loudness):
    if not text or not text.strip():
        raise gr.Error("Type some text to speak.")
    if not ref_audio:
        raise gr.Error("Upload or record a reference voice sample.")

    result_path = client.predict(
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

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"chatterbox_{timestamp}.wav")
    shutil.copy(result_path, out_path)
    return out_path


with gr.Blocks(title="Voicebox Lite - Cloud") as demo:
    gr.Markdown(
        "# \u26a1 Voicebox Lite (Cloud mode)\n"
        f"This sends your request to the free public **Chatterbox Turbo** Space "
        f"(`{SPACE_ID}`) and downloads the result here. Requires internet. "
        "Generation happens on their GPU, so it's much faster than running locally "
        "on this Mac - but you're sharing their free queue, so busy times may be slower."
    )

    with gr.Row():
        with gr.Column():
            text_in = gr.Textbox(
                label="Text to synthesize (max ~300 chars)",
                lines=5,
                value="Oh, that's hilarious! Anyway, let me tell you about this.",
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
            audio_out = gr.Audio(label="Result")
            gr.Markdown(f"Saved copies land in `{OUTPUT_DIR}`.")

    generate_btn.click(
        fn=generate,
        inputs=[text_in, ref_audio, temp, seed_num, min_p, top_p, top_k, repetition_penalty, norm_loudness],
        outputs=audio_out,
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861, inbrowser=True)