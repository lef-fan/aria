import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


class Stt:
    def __init__(self, params=None):
        self.params = params or {}
        self.device = self.params.get('device', None)
        self.model_name = self.params.get('model_name', None)
        self.low_cpu_mem_usage = self.params.get('low_cpu_mem_usage', None)
        self.attn = self.params.get('attn', None)
        
        if self.device == "cpu":
            self.attn = "sdpa"
            
        torch_dtype = torch.float16 if torch.cuda.is_available() and "cuda" in self.device else torch.float32
        
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=self.low_cpu_mem_usage,
            use_safetensors=True,
            attn_implementation=self.attn,
            device_map=self.device
        )
        
        processor = AutoProcessor.from_pretrained(self.model_name)
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            return_timestamps=True,
            torch_dtype=torch_dtype
        )

    def transcribe(self, data):
        data = data.numpy()
        data = self.pipe(
            data,
            generate_kwargs={"language": "en"}
        )
        data = data["text"]
        return data