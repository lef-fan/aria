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


def load_component(component_name, loader_func, params):
    """Safely load a component with error handling"""
    try:
        with show_status(f"Loading {component_name}..."):
            return loader_func(params)
    except Exception as e:
        rprint(f"[red]Error loading {component_name}: {str(e)}[/red]")
        rprint("[yellow]Please check your dependencies and model paths.[/yellow]")
        sys.exit(1)


def start_ollama_server(model_name: str):
    """Start the Ollama-based server with specified model"""
    # Load configuration
    with show_status("Loading configuration..."):
        config = load_config()

    # Setup model directories
    rprint("\n[bold cyan]Setting up model storage...[/bold cyan]")
    models_dir = setup_models_directory()

    # Update config paths with new model directory
    config.vad.repo_or_dir = str(models_dir / "vad")
    config.stt.model_name = str(models_dir / "stt" / Path(config.stt.model_name).name)
    config.tts.model_name = str(models_dir / "tts" / Path(config.tts.model_name).name)

    # Initialize components with updated paths and error handling
    rprint("\n[bold cyan]Initializing components...[/bold cyan]")

    nw = load_component("network", lambda p: Nw(params=p), config.network.dict())
    vad = load_component("VAD", lambda p: Vad(params=p), config.vad.dict())
    stt = load_component("STT", lambda p: Stt(params=p), config.stt.dict())
    tts = load_component("TTS", lambda p: Tts(params=p), config.tts.dict())
    llm = load_component("Ollama", lambda _: LlmOllama(model_name=model_name), None)

    # Network setup
    with show_status("Initializing network..."):
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
            llm_data = llm.get_answer(nw, tts, stt_data)
            if not llm.streaming_output:
                nw.send_msg(llm_data)
                txt_for_tts = remove_emojis(
                    remove_multiple_dots(remove_code_blocks(llm_data))
                )
                tts.run_tts(nw, txt_for_tts)
        elif client_data == "fixed_answer":
            tts.run_tts(nw, "Did you say something?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ollama Server for Aria")
    parser.add_argument("--model", default="llama2", help="Model name to use")
    args = parser.parse_args()

    start_ollama_server(args.model)
