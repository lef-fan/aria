import sys
import logging
import argparse
import numpy as np
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from components.nw import Nw
from components.vad import Vad
from components.stt import Stt
from components.llm_ollama import LlmOllama
from components.tts_server import Tts
from components.utils import (
    remove_emojis,
    remove_multiple_dots,
    remove_code_blocks,
)
from configs.configs import load_config
from cli.models_manager import setup_models_directory
from utils.progress import track_progress, show_status
from rich import print as rprint

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aria with Ollama")
    parser.add_argument(
        "--config",
        default="default.json",
        help="Path to JSON config file in the configs folder",
    )
    parser.add_argument("--model", default="llama2", help="Ollama model name to use")
    args = parser.parse_args()

    # Load configuration and setup models directory
    with show_status("Loading configuration..."):
        config = load_config(args.config)

    rprint("\n[bold cyan]Setting up model storage...[/bold cyan]")
    models_dir = setup_models_directory()

    # Update model paths
    vad_params = config.vad.model_dump()
    stt_params = config.stt.model_dump()
    tts_params = config.tts.model_dump()

    # Special handling for VAD model path
    vad_model_path = models_dir / "vad" / "silero_vad.onnx"
    if vad_model_path.exists():
        vad_params["repo_or_dir"] = str(models_dir / "vad")

    # Update paths for STT and TTS models
    stt_model_id = stt_params["model_name"]
    if not stt_model_id.startswith(("openai/", "facebook/", "microsoft/", "google/")):
        stt_params["model_name"] = str(models_dir / "stt" / Path(stt_model_id).name)

    tts_model_id = tts_params["model_name"]
    if not tts_model_id.startswith("tts_models/"):
        tts_params["model_name"] = str(models_dir / "tts" / Path(tts_model_id).name)

    # Initialize components
    rprint("\n[bold cyan]Initializing components...[/bold cyan]")

    with show_status("Loading network component..."):
        nw = Nw(params=config.network.model_dump())

    with show_status("Loading VAD model..."):
        vad = Vad(params=vad_params)

    with show_status("Loading STT model..."):
        stt = Stt(params=stt_params)

    with show_status("Loading Ollama LLM..."):
        llm = LlmOllama(model_name=args.model)

    with show_status("Loading TTS model..."):
        tts = Tts(params=tts_params)

    # Network setup
    nw.server_init()
    if nw.audio_compression:
        nw.init_audio_encoder(
            config.ap.samplerate, config.ap.channels, config.ap.buffer_size
        )
        nw.init_audio_decoder(
            config.mic.samplerate, config.mic.channels, config.mic.buffer_size
        )

    rprint("\n[bold green]✓ Server initialized successfully![/bold green]")
    rprint("[bold cyan]Waiting for client connection...[/bold cyan]")

    client_address = nw.server_listening()

    # Main server loop
    while True:
        try:
            client_data = nw.receive_msg()
        except:
            client_data = False

        if not client_data:
            print("Client disconnected...")
            client_address = nw.server_listening()
            continue

        if client_data == "reset_vad":
            vad.reset_vad()
            nw.send_ack()
        elif client_data == "vad_time":
            vad_time = vad.no_voice_wait_sec - vad.no_voice_sec
            nw.send_msg(vad_time)
        elif client_data == "vad_check":
            nw.send_ack()
            mic_chunk = nw.receive_audio_chunk(
                config.mic.buffer_size * 2  # 2 bytes per sample when pcm16
            )
            chunk_time = config.mic.buffer_size / config.mic.samplerate
            vad_status = vad.check(
                np.frombuffer(mic_chunk, np.int16)
                .flatten()
                .astype(np.float32, order="C")
                / 32768.0,
                chunk_time,
            )
            nw.send_msg(vad_status)
        elif client_data == "stt_transcribe":
            nw.send_ack()
            mic_recording = nw.receive_audio_recording()
            stt_data = stt.transcribe_translate(
                np.frombuffer(mic_recording, np.int16)
                .flatten()
                .astype(np.float32, order="C")
                / 32768.0
            )
            nw.send_msg(stt_data)
        elif client_data == "llm_get_answer":
            stt_text = stt_data  # ensure stt_data is set
            llm_data = llm.get_answer(nw, tts, stt_text)
            # If not streaming, send the text then do TTS
            if not llm.streaming_output:
                nw.send_msg(llm_data)
                txt_for_tts = remove_emojis(
                    remove_multiple_dots(remove_code_blocks(llm_data))
                )
                tts.run_tts(nw, txt_for_tts)
            else:
                # Streaming is handled in LlmOllama
                pass
        elif client_data == "fixed_answer":
            tts.run_tts(nw, "Did you say something?")
