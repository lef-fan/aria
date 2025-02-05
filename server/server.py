import sys
import logging
import argparse
import json
import numpy as np
from pathlib import Path
from os.path import join

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from components.nw import Nw
from components.vad import Vad
from components.stt import Stt
from components.llm_server import Llm
from components.tts_server import Tts
from components.utils import (
    remove_emojis,
    remove_multiple_dots,
    remove_code_blocks,
)
from cli.models_manager import setup_models_directory
from utils.progress import track_progress, show_status
from rich import print as rprint

# Set logging level
logging.basicConfig(level=logging.INFO)


def load_config(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    return json_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aria.")
    parser.add_argument(
        "--config",
        default="default.json",
        help="Path to JSON config file in the configs folder",
    )
    args = parser.parse_args()

    config_path = join("configs", args.config)
    config = load_config(config_path)

    # Setup model directories before initializing components
    rprint("\n[bold cyan]Setting up model storage...[/bold cyan]")
    models_dir = setup_models_directory()

    # Update model paths in config
    vad_params = config.get("Vad", {}).get("params", {})
    stt_params = config.get("Stt", {}).get("params", {})
    tts_params = config.get("Tts", {}).get("params", {})

    # Special handling for VAD model path - keep the original repo if path doesn't exist
    vad_model_path = models_dir / "vad" / "silero_vad.onnx"
    if vad_model_path.exists():
        vad_params["repo_or_dir"] = str(models_dir / "vad")
    # else keep the original GitHub repo path for first-time download

    # Keep HuggingFace model IDs as they are
    stt_model_id = stt_params["model_name"]  # Keep original HF model ID
    if not stt_model_id.startswith(("openai/", "facebook/", "microsoft/", "google/")):
        stt_params["model_name"] = str(models_dir / "stt" / Path(stt_model_id).name)

    tts_model_id = tts_params["model_name"]  # Keep original model ID
    if not tts_model_id.startswith("tts_models/"):
        tts_params["model_name"] = str(models_dir / "tts" / Path(tts_model_id).name)

    # Initialize components with updated paths
    rprint("\n[bold cyan]Initializing components...[/bold cyan]")

    with show_status("Loading network component..."):
        nw = Nw(params=config.get("Nw", {}).get("params", {}))

    with show_status("Loading VAD model..."):
        vad = Vad(params=vad_params)

    with show_status("Loading STT model..."):
        stt = Stt(params=stt_params)

    with show_status("Loading LLM..."):
        llm = Llm(params=config.get("Llm", {}).get("params", {}))

    with show_status("Loading TTS model..."):
        tts = Tts(params=tts_params)

    mic_params = config.get("Mic", {}).get("params", {})
    ap_params = config.get("Ap", {}).get("params", {})

    print("Loading...")

    nw.server_init()
    if nw.audio_compression:
        nw.init_audio_encoder(
            ap_params.get("samplerate"),
            ap_params.get("channels"),
            ap_params.get("buffer_size"),
        )
        nw.init_audio_decoder(
            mic_params.get("samplerate"),
            mic_params.get("channels"),
            mic_params.get("buffer_size"),
        )
    client_address = nw.server_listening()

    while True:
        try:
            client_data = nw.receive_msg()
        except:
            client_data = False
        # print(client_data)
        if not client_data:
            print("Client disconnected...")
            # maybe reset vad?
            client_address = nw.server_listening()
        if client_data == "reset_vad":
            vad.reset_vad()
            nw.send_ack()
        elif client_data == "vad_time":
            vad_time = vad.no_voice_wait_sec - vad.no_voice_sec
            nw.send_msg(vad_time)
        elif client_data == "vad_check":
            nw.send_ack()
            mic_chunk = nw.receive_audio_chunk(
                mic_params.get("buffer_size", None) * 2  # 2 bytes per sample when pcm16
            )
            chunk_time = mic_params.get("buffer_size", None) / mic_params.get(
                "samplerate", None
            )
            vad_status = vad.check(
                np.frombuffer(mic_chunk, np.int16)
                .flatten()
                .astype(np.float32, order="C")
                / 32768.0,
                chunk_time,
            )
            # print(vad_status, vad.no_voice_sec)
            nw.send_msg(vad_status)
        elif client_data == "stt_transcribe":
            nw.send_ack()
            mic_recording = nw.receive_audio_recording()
            # wf.write(
            #     "test.wav",
            #     mic_params.get("samplerate", None),
            #     np.frombuffer(mic_recording, np.int16).flatten(),
            # )
            stt_data = stt.transcribe_translate(
                np.frombuffer(mic_recording, np.int16)
                .flatten()
                .astype(np.float32, order="C")
                / 32768.0
            )
            nw.send_msg(stt_data)
        elif client_data == "llm_get_answer":
            llm_data = llm.get_answer(nw, tts, stt_data)
            if not llm.streaming_output:
                nw.send_msg(llm_data)
                if tts.tts_type == "coqui":
                    tts.text_splitting = True
                # TODO handle emphasis
                txt_for_tts = remove_emojis(
                    remove_multiple_dots(remove_code_blocks(llm_data))
                )
                tts.run_tts(nw, txt_for_tts)
        elif client_data == "fixed_answer":
            tts.run_tts(nw, "Did you say something?")
