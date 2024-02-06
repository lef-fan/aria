import torch
import onnxruntime as ort


class Vad:
    """
    Voice Activity Detection (VAD) class.

    Args:
        params (dict): Parameters for VAD initialization.
            - samplerate (int): The sampling rate of the audio.
            - repo_or_dir (str): The repository or directory containing the VAD model.
            - model_name (str): The name of the VAD model.
            - force_reload (bool): Whether to force reload the VAD model.
            - use_onnx (bool): Whether to use ONNX format for the VAD model.
            - no_voice_wait_sec (int): The number of seconds to wait before considering the absence of voice.

    Attributes:
        params (dict): Parameters for VAD initialization.
        samplerate (int): The sampling rate of the audio.
        repo_or_dir (str): The repository or directory containing the VAD model.
        model_name (str): The name of the VAD model.
        force_reload (bool): Whether to force reload the VAD model.
        use_onnx (bool): Whether to use ONNX format for the VAD model.
        no_voice_wait_sec (int): The number of seconds to wait before considering the absence of voice.
        silero_vad_model: The loaded VAD model.
        silero_utils: Utility functions for VAD.
        get_speech_timestamps: Function to get speech timestamps from audio data.
        save_audio: Function to save audio data.
        read_audio: Function to read audio data.
        VADIterator: Iterator for VAD.
        collect_chunks: Function to collect audio chunks.

    Methods:
        check_data(data): Checks the audio data for voice activity.

    """

    def __init__(self, params=None):
        self.params = params or {}
        self.samplerate = self.params.get('samplerate', None)
        self.repo_or_dir = self.params.get('repo_or_dir', None)
        self.model_name = self.params.get('model_name', None)
        self.force_reload = self.params.get('force_reload', None)
        self.use_onnx = self.params.get('use_onnx', None)
        self.no_voice_wait_sec = self.params.get('no_voice_wait_sec', None)
        self.onnx_verbose = self.params.get('onnx_verbose', None)
        self.verbose = self.params.get('verbose', None)
        
        if self.use_onnx and not self.onnx_verbose:
            ort.set_default_logger_severity(3)
        
        self.silero_vad_model, self.silero_utils = torch.hub.load(
            repo_or_dir=self.repo_or_dir,
            model=self.model_name,
            force_reload=self.force_reload,
            onnx=self.use_onnx,
            trust_repo='check',
            verbose=self.verbose
        )
        
        (
            self.get_speech_timestamps,
            self.save_audio,
            self.read_audio,
            self.VADIterator,
            self.collect_chunks,
        ) = self.silero_utils

        self.no_voice_sec = 0
        self.voice_trigger = False

    def check(self, data):
        """
        Checks the audio data for voice activity.

        Args:
            data: The audio data to be checked.

        Returns:
            str: If voice gathering finished, returns "vad end". 
                Otherwise, returns the voice data to collect. 
                Returns None if there was no voice and had no voice activity already.

        """
        speech_timestamps = self.get_speech_timestamps(
            data,
            self.silero_vad_model,
            sampling_rate=self.samplerate
        )
        if len(speech_timestamps) > 0:
            self.voice_trigger = True
            self.no_voice_sec = 0
        else:
            if self.voice_trigger:
                self.no_voice_sec += 1
                if self.no_voice_sec == self.no_voice_wait_sec:
                    self.voice_trigger = False
                    self.no_voice_sec = 0
                    return "vad end"
            else:
                return None
        return data
