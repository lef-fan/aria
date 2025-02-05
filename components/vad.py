import torch
import onnxruntime as ort


class Vad:
    def __init__(self, params=None):
        self.params = params or {}
        self.samplerate = self.params.get("samplerate", None)
        self.repo_or_dir = self.params.get("repo_or_dir", None)
        self.model_name = self.params.get("model_name", None)
        self.force_reload = self.params.get("force_reload", None)
        self.use_onnx = self.params.get("use_onnx", None)
        self.no_voice_wait_sec = self.params.get("no_voice_wait_sec", None)
        self.onnx_verbose = self.params.get("onnx_verbose", None)
        self.verbose = self.params.get("verbose", None)

        if self.use_onnx and not self.onnx_verbose:
            ort.set_default_logger_severity(3)

        self.silero_vad_model, self.silero_utils = torch.hub.load(
            repo_or_dir=self.repo_or_dir,
            model=self.model_name,
            force_reload=self.force_reload,
            onnx=self.use_onnx,
            trust_repo="check",
            verbose=self.verbose,
        )

        (
            self.get_speech_timestamps,
            self.save_audio,
            self.read_audio,
            self.VADIterator,
            self.collect_chunks,
        ) = self.silero_utils

        self.no_voice_sec = 0

        self.vad_iterator = self.VADIterator(
            self.silero_vad_model,
            threshold=0.5,
            sampling_rate=self.samplerate,
            min_silence_duration_ms=100,
            speech_pad_ms=30,
        )

    def reset_vad(self):
        self.no_voice_sec = 0
        self.vad_iterator.reset_states()

    def check(self, mic_chunk, chunk_time):
        speech_dict = self.vad_iterator(
            mic_chunk[64:576],  # TODO grab target buffer size from mic
            return_seconds=False,  # can only do 256 8k or 512 for 16k, mid should be good?
        )
        if speech_dict is not None:
            if "start" in speech_dict:
                self.no_voice_sec = 0
            elif "end" in speech_dict:
                self.no_voice_sec += chunk_time
        else:
            if self.no_voice_sec != 0:
                self.no_voice_sec += chunk_time
                if self.no_voice_sec > self.no_voice_wait_sec:
                    self.no_voice_sec = 0
                    self.vad_iterator.reset_states()
                    return "vad_end"
            elif not self.vad_iterator.triggered:
                return "None"
        return "vad_continue"
