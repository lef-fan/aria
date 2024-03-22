import time
from copy import deepcopy
import pyaudio
import numpy as np
import soundfile as sf


class Ap:
    def __init__(self, params=None, ui=None):
        self.params = params or {}
        self.audio_device = self.params.get('audio_device', None)
        self.samplerate = self.params.get('samplerate', None)
        self.buffer_size = self.params.get('buffer_size', None)
        self.channels = self.params.get('channels', None)
        self.listening_sound_path = self.params.get('assets', None).get('listening_sound', None)
        self.transition_sound_path = self.params.get('assets', None).get('transition_sound', None)
        self.sample_format = pyaudio.paFloat32
        
        if self.audio_device == "default":
            self.audio_device = None
            
        self.ui = ui
        self.update_ui = False
        self.load_visual_once = True
        self.audio_buffer = None    
            
        p = pyaudio.PyAudio()
        self.stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.samplerate,
                        frames_per_buffer=self.buffer_size,
                        output=True,
                        output_device_index=self.audio_device,
                        stream_callback=self._callback
                        )
        
        self.listening_sound, self.listening_sound_sr = sf.read(self.listening_sound_path)
        self.transition_sound, self.transition_sound_sr = sf.read(self.transition_sound_path)
        
    def _callback(self, in_data, frame_count, time_info, status):
        if self.audio_buffer is None:
            data = np.zeros(frame_count)
        elif len(self.audio_buffer) >= frame_count:
            data = self.audio_buffer[:frame_count]
            self.audio_buffer = self.audio_buffer[frame_count:]
        else:
            shortfall = frame_count - len(self.audio_buffer)
            data = np.concatenate((self.audio_buffer, np.zeros(shortfall, dtype=np.float32)))
            self.audio_buffer = None
        if self.update_ui:
            self.ui.update_visual("Aria", data)
        return (data.tobytes(), pyaudio.paContinue)
    
    def check_audio_finished(self):
        time.sleep(len(self.audio_buffer) / self.samplerate)
        self.update_ui = False
        self.load_visual_once = True
        
    def stream_sound(self, chunk, update_ui=False):
        if update_ui and self.load_visual_once:
            self.ui.load_visual("Aria")
            self.load_visual_once = False
        self.update_ui = update_ui
        if self.audio_buffer is None:
            self.audio_buffer = deepcopy(chunk)
        else:
            self.audio_buffer = np.concatenate((self.audio_buffer, chunk))
        
    def play_sound(self, sound):
        for chunk_index in range(0, len(sound), self.buffer_size):
            chunk = sound[chunk_index:chunk_index + self.buffer_size]
            chunk = np.mean(chunk, axis=1)
            self.stream_sound(chunk.astype('float32'))
        self.check_audio_finished()
