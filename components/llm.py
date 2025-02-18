import sys
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from .utils import remove_emojis
from .utils import remove_nonverbal_cues


class Llm:
    def __init__(self, params=None):
        self.params = params or {}
        self.custom_path = self.params.get("custom_path", None)
        self.model_name = self.params.get("model_name", None)
        self.model_file = self.params.get("model_file", None)
        self.num_gpu_layers = self.params.get("num_gpu_layers", None)
        self.context_length = self.params.get("context_length", None)
        self.streaming_output = self.params.get("streaming_output", None)
        self.chat_format = self.params.get("chat_format", None)
        self.system_message = self.params.get("system_message", None)
        self.verbose = self.params.get("verbose", None)

        if self.custom_path != "":
            model_path = self.custom_path
        elif isinstance(self.model_file, list):
            for model_path_split in self.model_file:
                model_path = hf_hub_download(self.model_name, filename=model_path_split)
        else:
            model_path = hf_hub_download(self.model_name, filename=self.model_file)

        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=self.num_gpu_layers,
            n_ctx=self.context_length,
            chat_format=self.chat_format,
            verbose=self.verbose,
        )

        self.messages = [{"role": "system", "content": self.system_message}]

    def get_answer(self, ui, ap, tts, data):
        self.messages.append({"role": "user", "content": data})

        outputs = self.llm.create_chat_completion(
            self.messages, stream=self.streaming_output
        )

        if self.streaming_output:
            llm_output = ""
            tts_text_buffer = []
            color_code_block = False
            backticks = 0
            skip_code_block_on_tts = False
            ui.add_message("Aria", "", new_entry=True)
            for i, out in enumerate(outputs):
                if "content" in out["choices"][0]["delta"]:
                    output_chunk_txt = out["choices"][0]["delta"]["content"]
                    if (
                        output_chunk_txt == "```" and backticks == 0
                    ):  # 3 for qwen, 2 for mixtral ?
                        skip_code_block_on_tts = not skip_code_block_on_tts
                        color_code_block = not color_code_block
                        backticks += 3  # 3 for qwen, 2 for mixtral ?
                    if backticks > 0 and backticks <= 3:
                        backticks += 1
                    else:
                        backticks = 0
                    if i == 1:
                        print("Aria:", output_chunk_txt.strip(), end="")
                        if backticks == 0:
                            ui.add_message(
                                "Aria",
                                output_chunk_txt.strip(),
                                new_entry=False,
                                color_code_block=color_code_block,
                            )
                    else:
                        print(output_chunk_txt, end="")
                        if backticks == 0:
                            ui.add_message(
                                "Aria",
                                output_chunk_txt,
                                new_entry=False,
                                color_code_block=color_code_block,
                            )
                    sys.stdout.flush()
                    llm_output += output_chunk_txt
                    if not skip_code_block_on_tts:
                        tts_text_buffer.append(output_chunk_txt)
                        if tts_text_buffer[-1] in [".", "!", "?", ":", "..", "..."]:
                            # TODO handle float numbers
                            # TODO remove multi dots
                            # TODO handle emphasis
                            txt_for_tts = remove_nonverbal_cues(
                                    remove_emojis(
                                    "".join(tts_text_buffer).strip()
                                    )
                                )
                            if len(txt_for_tts) > 1 and not all(
                                char.isspace() for char in txt_for_tts
                            ):
                                tts.run_tts(txt_for_tts)
                            tts_text_buffer = []
            if not skip_code_block_on_tts and len(tts_text_buffer) != 0:
                # TODO remove multi dots
                txt_for_tts = remove_nonverbal_cues(remove_emojis("".join(tts_text_buffer).strip()))
                if len(txt_for_tts) > 1 and not all(
                    char.isspace() for char in txt_for_tts
                ):
                    tts.run_tts(txt_for_tts)
            ap.check_audio_finished()
            print()
            llm_output = llm_output.strip()
        else:
            llm_output = outputs["choices"][0]["message"]["content"].strip()

        self.messages.append({"role": "assistant", "content": llm_output})

        return llm_output
