from copy import deepcopy
import pyaudio


class mic:
    def __init__(self, params=None):
        self.samplerate = self.params.get('samplerate', None)
        self.buffer_size = self.params.get('buffer_size', None)
        self.channels = self.params.get('channels', None)
        self.sample_format = pyaudio.paInt16
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.samplerate,
            frames_per_buffer=self.buffer_size,
            input=True,
            stream_callback=self._update_data,
        )
        
        self.data = None

    def _update_data(self, in_data, frame_count, time_info, status):
        self.data = deepcopy(in_data)
        return (in_data, pyaudio.paContinue)

    def get_data(self):
        return self.data
    
    def start_mic(self):
        self.stream.start_stream()
    
    def stop_mic(self):
        self.stream.stop_stream()
