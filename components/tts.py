import os
import warnings
import numpy as np
from trainer.io import get_user_data_dir
from TTS.utils.manage import ModelManager
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from kokoro import KPipeline


class Tts:
    def __init__(self, params=None, ap=None):
        self.params = params or {}
        self.device = self.params.get("device", None)
        self.tts_type = self.params.get("tts_type", None)
        self.use_deepspeed = self.params.get("use_deepspeed", None)
        self.text_splitting = self.params.get("text_splitting", None)
        self.model_name = self.params.get("model_name", None)
        self.force_reload = self.params.get("force_reload", None)
        self.verbose = self.params.get("verbose", None)
        self.kokoro_voice = self.params.get("kokoro_voice", None)
        self.kokoro_voice_speed = self.params.get("kokoro_voice_speed", None)
        self.voice_to_clone = self.params.get("assets", None).get(
            "voice_to_clone", None
        )

        self.ap = ap

        if self.tts_type == "coqui":
            if not self.verbose:
                warnings.filterwarnings("ignore", module="TTS")

            self.model_path = os.path.join(
                get_user_data_dir("tts"), self.model_name.replace("/", "--")
            )
            if self.force_reload or not os.path.isdir(self.model_path):
                self.model_manager = ModelManager()
                self.model_path, _, _ = self.model_manager.download_model(self.model_name)

            self.config = XttsConfig()
            self.config.load_json(os.path.join(self.model_path, "config.json"))
            self.model = Xtts.init_from_config(self.config)
            self.model.load_checkpoint(
                self.config,
                checkpoint_dir=self.model_path,
                use_deepspeed=self.use_deepspeed,
            )
            if self.device == "gpu":
                self.model.cuda()
            # self.model.eval() # do we need to force eval here as the load above didnt?

            self.gpt_cond_latent, self.speaker_embedding = (
                self.model.get_conditioning_latents(audio_path=[self.voice_to_clone])
            )
        elif self.tts_type == "kokoro":
            self.pipeline = KPipeline(lang_code='a')

    def run_tts(self, data):
        if self.tts_type == "coqui":
            tts_stream = self.model.inference_stream(
                data,
                "en",
                self.gpt_cond_latent,
                self.speaker_embedding,
                enable_text_splitting=self.text_splitting,
            )
        elif self.tts_type == "kokoro":
            tts_stream = self.pipeline(
                    data, voice=self.kokoro_voice,
                    speed=self.kokoro_voice_speed, split_pattern=r'\n+'
                )
        for chunk in tts_stream:
            if self.tts_type == "kokoro":
                chunk = chunk[-1].squeeze()
            else:
                chunk = chunk.squeeze()
            if self.device == "gpu":
                chunk = chunk.cpu()
            self.ap.stream_sound(
                (chunk.numpy() * 32768).astype(np.int16), update_ui=True
            )

        return "tts_done"
