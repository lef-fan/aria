# from copy import deepcopy
import numpy as np
import pyaudio


class Mic:
    def __init__(self, params=None):
        self.params = params or {}
        self.samplerate = self.params.get('samplerate', None)
        self.buffer_size = self.params.get('buffer_size', None)
        self.channels = self.params.get('channels', None)
        self.device = self.params.get('device', None)
        self.sample_format = pyaudio.paFloat32
        
        if self.device == "default":
            self.device = None
        
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.samplerate,
            frames_per_buffer=self.buffer_size,
            input=True,
            input_device_index=self.device,
            # stream_callback=self._update_data,
        )
        
        self.data = None

    def _update_data(self, in_data, frame_count, time_info, status):
        self.data = np.frombuffer(in_data, np.float32).flatten()
        return (in_data, pyaudio.paContinue)

    def get_data(self):
        # return self.data
        self.data = self.stream.read(self.buffer_size)
        return np.frombuffer(self.data, np.float32).flatten()
    
    def start_mic(self):
        self.stream.start_stream()
    
    def stop_mic(self):
        self.stream.stop_stream()
