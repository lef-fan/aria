import os
import time
import warnings
import pyaudio
import numpy as np
from TTS.utils.generic_utils import get_user_data_dir
from TTS.utils.manage import ModelManager
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts


class Tts:
    def __init__(self, params=None):
        self.params = params or {}
        self.audio_device = self.params.get('audio_device', None)
        self.device = self.params.get('device', None)
        self.samplerate = self.params.get('samplerate', None)
        self.buffer_size = self.params.get('buffer_size', None)
        self.channels = self.params.get('channels', None)
        self.use_deepspeed = self.params.get('use_deepspeed', None)
        self.text_splitting = self.params.get('text_splitting', None)
        self.model_name = self.params.get('model_name', None)
        self.force_reload = self.params.get('force_reload', None)
        self.verbose = self.params.get('verbose', None)
        self.voice_to_clone = self.params.get('assets', None).get('voice_to_clone', None)
        self.sample_format = pyaudio.paFloat32
        
        if self.audio_device == "default":
            self.audio_device = None

        p = pyaudio.PyAudio()
        self.stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.samplerate,
                        frames_per_buffer=self.buffer_size,
                        output=True,
                        output_device_index=self.audio_device,
                        stream_callback=self._callback
                        )
        
        self.audio_buffer = None
        self.ui = None
        
        if not self.verbose:
            warnings.filterwarnings("ignore", module="TTS")

        self.model_path = os.path.join(get_user_data_dir("tts"), self.model_name.replace('/', '--'))
        if self.force_reload or not os.path.isdir(self.model_path):
            self.model_manager = ModelManager(verbose=self.verbose)
            self.model_path, _, _ = self.model_manager.download_model(self.model_name)  
            
        self.config = XttsConfig()
        self.config.load_json(os.path.join(self.model_path, 'config.json'))
        self.model = Xtts.init_from_config(self.config)
        self.model.load_checkpoint(self.config, 
                            checkpoint_dir=self.model_path, 
                            use_deepspeed=self.use_deepspeed)
        if self.device == 'gpu':
            self.model.cuda()

        self.gpt_cond_latent, self.speaker_embedding = self.model.get_conditioning_latents(
                audio_path=[self.voice_to_clone]
            )
    
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
        if self.ui is not None:
            self.ui.update_visual("Aria", data)
        return (data.tobytes(), pyaudio.paContinue)
    
    def run_tts(self, ui, data):
        self.ui = ui
        tts_stream = self.model.inference_stream(
                data,
                "en",
                self.gpt_cond_latent,
                self.speaker_embedding,
                enable_text_splitting=self.text_splitting
            )
        for chunk in tts_stream:
            chunk = chunk.squeeze()
            if self.device == 'gpu':
                chunk = chunk.cpu()
            if self.audio_buffer is None:
                self.audio_buffer = chunk.numpy()
            else:
                self.audio_buffer = np.concatenate((self.audio_buffer, chunk.numpy()))
        
        return 'tts_done'
    
    def check_audio_finished(self):
        time.sleep(len(self.audio_buffer) / self.samplerate)  
