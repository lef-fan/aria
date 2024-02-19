import sys
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from .utils import remove_emojis


class Llm:
    def __init__(self, params=None):
        self.params = params or {}
        self.model_name = self.params.get('model_name', None)
        self.model_file = self.params.get('model_file', None)
        self.num_gpu_layers = self.params.get('num_gpu_layers', None)
        self.context_length = self.params.get('context_length', None)
        self.streaming_output = self.params.get('streaming_output', None)
        self.chat_format = self.params.get('chat_format', None)
        self.system_message = self.params.get('system_message', None)
        self.verbose = self.params.get('verbose', None)
       
        model_path = hf_hub_download(self.model_name, filename=self.model_file)

        self.llm = Llama(
                    model_path=model_path,
                    n_gpu_layers=self.num_gpu_layers,
                    n_ctx=self.context_length,
                    chat_format=self.chat_format,
                    verbose=self.verbose
                    )

        self.messages = [
                {
                    "role": "system", 
                    "content": self.system_message
                }
            ]

    def get_answer(self, ui, tts, data):
        self.messages.append(
            {
                "role": "user", 
                "content": data
            }
        )
    
        outputs = self.llm.create_chat_completion(
            self.messages,
            stream=self.streaming_output
            )
        ui.load_visual("Aria")
        
        if self.streaming_output:
            llm_output = ""
            tts_text_buffer = []
            color_code_block = False
            skip_code_block_on_tts = False
            ui.add_message("Aria", "", new_entry=True)
            for i, out in enumerate(outputs):
                if "content" in out['choices'][0]["delta"]:
                    output_chunk_txt = out['choices'][0]["delta"]['content']
                    if output_chunk_txt == "``": # TODO remove the remaining backticks in ui
                        skip_code_block_on_tts = not skip_code_block_on_tts
                        color_code_block = not color_code_block
                    if i == 1:
                        print('Aria:', output_chunk_txt.strip(), end='')
                        ui.add_message("Aria", output_chunk_txt.strip(), new_entry=False, color_code_block=color_code_block)
                    else:
                        print(output_chunk_txt, end='')
                        ui.add_message("Aria", output_chunk_txt, new_entry=False, color_code_block=color_code_block)
                    sys.stdout.flush()
                    llm_output += output_chunk_txt
                    if not skip_code_block_on_tts:
                        tts_text_buffer.append(output_chunk_txt)
                        if tts_text_buffer[-1] in [".", "!", "?", ":", "..", "..."]:
                            tts.run_tts(ui, remove_emojis("".join(tts_text_buffer).strip())) # TODO remove multi dots
                            tts_text_buffer = []
            if not skip_code_block_on_tts and len(tts_text_buffer) != 0:
                tts.run_tts(ui, remove_emojis("".join(tts_text_buffer).strip())) # TODO remove multi dots
            tts.check_audio_finished()
            print()
            llm_output = llm_output.strip()
        else:
            llm_output = outputs["choices"][0]["message"]["content"].strip()

        self.messages.append(
            {
                "role": "assistant", 
                "content": llm_output
            }
        )
        
        return llm_output