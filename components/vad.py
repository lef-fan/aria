import torch


class Vad:
    def __init__(self, params=None):
        self.params = params or {}
        self.device = self.params.get('device', None)
        self.samplerate = self.params.get('samplerate', None)
        self.no_voice_wait_sec = self.params.get('no_voice_wait_sec', None)
        
        self.silero_vad_model, self.silero_utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False
        )
        self.silero_vad_model = self.silero_vad_model.to(self.device)
        
        (
            self.get_speech_timestamps,
            self.save_audio,
            self.read_audio,
            self.VADIterator,
            self.collect_chunks,
        ) = self.silero_utils

        self.no_voice_sec = 0
        self.voice_trigger = False

    def check_data(self, data):
        speech_timestamps = self.get_speech_timestamps(
            data.to(self.device),
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
