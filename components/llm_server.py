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

    def get_answer(self, nw, tts, data):
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
        
        if self.streaming_output:
            llm_output = ""
            tts_text_buffer = []
            color_code_block = False
            backticks = 0
            skip_code_block_on_tts = False
            nw.send_ack()
            for i, out in enumerate(outputs):
                if "content" in out['choices'][0]["delta"]:
                    output_chunk_txt = out['choices'][0]["delta"]['content']
                    if output_chunk_txt == "``" and backticks == 0:
                        skip_code_block_on_tts = not skip_code_block_on_tts
                        color_code_block = not color_code_block
                        backticks += 2
                    if backticks > 0 and backticks <= 3:
                        backticks += 1
                    else:
                        backticks = 0
                    if i == 1:
                        if backticks == 0:
                            nw.receive_ack()
                            nw.send_msg("llm")
                            nw.receive_ack()
                            nw.send_msg(str(len(output_chunk_txt.strip().encode())))
                            nw.receive_ack()
                            nw.send_msg(output_chunk_txt.strip())
                            nw.receive_ack()
                            nw.send_msg(str(color_code_block))
                    else:
                        if backticks == 0:
                            nw.receive_ack()
                            nw.send_msg("llm")
                            nw.receive_ack()
                            nw.send_msg(str(len(output_chunk_txt.encode())))
                            nw.receive_ack()
                            nw.send_msg(output_chunk_txt)
                            nw.receive_ack()
                            nw.send_msg(str(color_code_block))
                    llm_output += output_chunk_txt
                    if not skip_code_block_on_tts:
                        tts_text_buffer.append(output_chunk_txt)
                        if tts_text_buffer[-1] in [".", "!", "?", ":", "..", "..."]:
                            # TODO handle float numbers
                            # TODO remove multi dots
                            # TODO handle emphasis
                            txt_for_tts = remove_emojis("".join(tts_text_buffer).strip())
                            if len(txt_for_tts) > 1:
                                nw.receive_ack()
                                nw.send_msg("tts")
                                tts.run_tts(nw, txt_for_tts)
                            tts_text_buffer = []
            if not skip_code_block_on_tts and len(tts_text_buffer) != 0:
                # TODO remove multi dots
                txt_for_tts = remove_emojis("".join(tts_text_buffer).strip())
                if len(txt_for_tts) > 1:
                    nw.receive_ack()
                    nw.send_msg("tts")
                    tts.run_tts(nw, txt_for_tts)
            nw.receive_ack()
            nw.send_msg("streaming_end")
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