from pydantic import BaseModel, Field
from typing import Optional, Dict
from pathlib import Path


class MicConfig(BaseModel):
    audio_device: str = Field(default="default", description="Audio input device")
    samplerate: int = Field(default=16000, description="Audio sample rate")
    buffer_size: int = Field(default=640, description="Audio buffer size")
    channels: int = Field(default=1, description="Number of audio channels")


class VadConfig(BaseModel):
    samplerate: int = Field(default=16000, description="VAD sample rate")
    repo_or_dir: str = Field(
        default="snakers4/silero-vad", description="Model repository"
    )
    model_name: str = Field(default="silero_vad", description="VAD model name")
    force_reload: bool = Field(default=False, description="Force model reload")
    use_onnx: bool = Field(default=True, description="Use ONNX runtime")
    no_voice_wait_sec: float = Field(
        default=1.0, description="No voice timeout in seconds"
    )
    onnx_verbose: bool = Field(default=False, description="ONNX verbose output")
    verbose: bool = Field(default=False, description="Verbose output")


class SttConfig(BaseModel):
    device: str = Field(default="cuda:0", description="Computing device")
    model_name: str = Field(
        default="openai/whisper-large-v3", description="STT model name"
    )
    low_cpu_mem_usage: bool = Field(default=True, description="Low CPU memory usage")
    attn: str = Field(default="flash_attention_2", description="Attention mechanism")
    verbose: bool = Field(default=False, description="Verbose output")


class LlmConfig(BaseModel):
    custom_path: str = Field(default="", description="Custom model path")
    model_name: str = Field(
        default="bartowski/Qwen2.5-32B-AGI-GGUF", description="Model name"
    )
    model_file: str = Field(
        default="Qwen2.5-32B-AGI-Q5_K_M.gguf", description="Model file"
    )
    num_gpu_layers: int = Field(default=-1, description="Number of GPU layers")
    context_length: int = Field(default=8000, description="Context length")
    streaming_output: bool = Field(default=True, description="Enable streaming output")
    chat_format: str = Field(default="qwen", description="Chat format")
    system_message: str = Field(
        default="You are Aria an AI entity. You are rude, sarcastic and funny. "
        "Please aim for concise responses, limiting them to a maximum of 20 words whenever possible. "
        "Please do not suggest for further assistance or help.",
        description="System message",
    )
    verbose: bool = Field(default=False, description="Verbose output")


class TtsAssets(BaseModel):
    voice_to_clone: Path = Field(
        default=Path("assets/sofia_hellen.wav"), description="Voice to clone file"
    )


class TtsConfig(BaseModel):
    device: str = Field(default="gpu", description="Computing device")
    tts_type: str = Field(default="kokoro", description="TTS type")
    use_deepspeed: bool = Field(default=False, description="Use DeepSpeed")
    text_splitting: bool = Field(default=False, description="Enable text splitting")
    model_name: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        description="TTS model name",
    )
    force_reload: bool = Field(default=False, description="Force model reload")
    verbose: bool = Field(default=False, description="Verbose output")
    kokoro_voice: str = Field(default="af_heart", description="Kokoro voice")
    assets: TtsAssets = Field(default_factory=TtsAssets)


class ApAssets(BaseModel):
    listening_sound: Path = Field(
        default=Path("assets/listening.wav"), description="Listening sound file"
    )
    transition_sound: Path = Field(
        default=Path("assets/transition.wav"), description="Transition sound file"
    )


class ApConfig(BaseModel):
    audio_device: str = Field(default="default", description="Audio output device")
    samplerate: int = Field(default=24000, description="Audio sample rate")
    buffer_size: int = Field(default=960, description="Audio buffer size")
    channels: int = Field(default=1, description="Number of audio channels")
    assets: ApAssets = Field(default_factory=ApAssets)


class UiAssets(BaseModel):
    icon: Path = Field(default=Path("assets/aria_icon.png"), description="UI icon file")
    loading_gif: Path = Field(
        default=Path("assets/loading.gif"), description="Loading animation"
    )
    transition_gif: Path = Field(
        default=Path("assets/transition.gif"), description="Transition animation"
    )
    muted_mic_gif: Path = Field(
        default=Path("assets/muted_mic.gif"), description="Muted microphone animation"
    )


class UiConfig(BaseModel):
    window_title: str = Field(default="Aria", description="Window title")
    window_size: str = Field(default="750", description="Window size")
    assets: UiAssets = Field(default_factory=UiAssets)


class NetworkConfig(BaseModel):
    audio_compression: bool = Field(
        default=True, description="Enable audio compression"
    )
    host_ip: str = Field(default="0.0.0.0", description="Host IP address")
    port: int = Field(default=12345, description="Host port")
    client_target_ip: str = Field(default="0.0.0.0", description="Client target IP")
    client_target_port: int = Field(default=12345, description="Client target port")


class AriaConfig(BaseModel):
    mic: MicConfig = Field(default_factory=MicConfig)
    vad: VadConfig = Field(default_factory=VadConfig)
    stt: SttConfig = Field(default_factory=SttConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    tts: TtsConfig = Field(default_factory=TtsConfig)
    ap: ApConfig = Field(default_factory=ApConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)

    @classmethod
    def from_json(cls, json_path: Path) -> "AriaConfig":
        """Load configuration from JSON file"""
        return cls.parse_file(json_path)

    def to_json(self, json_path: Path) -> None:
        """Save configuration to JSON file"""
        json_path.write_text(self.json(indent=2))


def load_config(config_path: str = "default.json") -> AriaConfig:
    """Load configuration from the configs directory"""
    config_file = Path(__file__).parent / config_path
    return AriaConfig.from_json(config_file)
