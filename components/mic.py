import numpy as np
import pyaudio


class Mic:
    def __init__(self, params=None, ui=None, vad=None):
        self.params = params or {}
        self.audio_device = self.params.get("audio_device", None)
        self.samplerate = self.params.get("samplerate", None)
        self.buffer_size = self.params.get("buffer_size", None)
        self.channels = self.params.get("channels", None)
        self.sample_format = pyaudio.paInt16
        self.bytes_per_second = (
            self.samplerate * 2 * self.channels
        )  # 2 bytes per sample when pcm16

        if self.audio_device == "default":
            self.audio_device = None

        self.ui = ui
        self.update_ui = False
        self.vad_time = vad.no_voice_wait_sec

        p = pyaudio.PyAudio()
        self._stream = p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.samplerate,
            frames_per_buffer=self.buffer_size,
            input=True,
            input_device_index=self.audio_device,
            stream_callback=self._callback,
            start=False,
        )

        self._chunk_buffer = bytes()
        self._recording_buffer = bytearray()

    def _callback(self, in_data, frame_count, time_info, status):
        self._chunk_buffer = in_data
        self._recording_buffer.extend(self._chunk_buffer)
        # self._recording_buffer.extend(in_data)
        if self.update_ui:
            self.ui.update_visual(
                "You",
                np.frombuffer(self._chunk_buffer, np.int16)
                .flatten()
                .astype(np.float32, order="C")
                / 32768.0,
                time_color_warning=self.vad_time,
            )
        # return (in_data, pyaudio.paContinue)
        return (self._chunk_buffer, pyaudio.paContinue)

    def get_recording(self):
        # return np.frombuffer(self._recording_buffer, np.float32).flatten()
        return bytes(self._recording_buffer)

    def get_chunk(self):
        # return np.frombuffer(self._chunk_buffer, np.float32).flatten()
        # return np.frombuffer(
        #     self._recording_buffer[-(self.buffer_size * 4) :], np.float32
        # ).flatten()
        # return self._recording_buffer[-(self.buffer_size * 2) :]
        return self._chunk_buffer

    def start_mic(self):
        self.update_ui = True
        self._chunk_buffer = bytes()
        self._recording_buffer = bytearray()
        self._stream.start_stream()

    def stop_mic(self):
        self._stream.stop_stream()
        self.update_ui = False

    def reset_recording(self):
        # self._recording_buffer = bytearray()
        # make sure we keep the last second before reset to avoid losing speech on next run
        if len(self._recording_buffer) >= self.bytes_per_second:
            last_second = self._recording_buffer[-self.bytes_per_second :]
        else:
            last_second = self._recording_buffer
        self._recording_buffer = bytearray()
        self._recording_buffer.extend(last_second)
