import os
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

        p = pyaudio.PyAudio()
        self.stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.samplerate,
                        frames_per_buffer=self.buffer_size,
                        output=True
                        )
        
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

    def audio_stream(self, buffer):
        self.stream.write(buffer.tobytes())

    def run_tts(self, data):
        tts_stream = self.model.inference_stream(
                data,
                "en",
                self.gpt_cond_latent,
                self.speaker_embedding,
                enable_text_splitting=self.text_splitting
            )
        for chunk in tts_stream:
            chunk_length = chunk.shape[-1]
            chunk = chunk.squeeze()
            if self.device == 'gpu':
                chunk = chunk.cpu()
            self.audio_stream(chunk.numpy())
        if chunk_length < self.buffer_size:
            chunk = np.zeros(self.buffer_size - chunk_length)
            self.audio_stream(chunk)
        
        return 'tts done'