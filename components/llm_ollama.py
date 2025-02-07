import ollama
from components.utils import remove_emojis, remove_multiple_dots, remove_code_blocks
import re


class LlmOllama:
    def __init__(self, model_name: str):
        self.model = model_name
        self.streaming_output = True

    def get_answer(self, nw, tts, prompt: str) -> str:
        try:
            full_response = ""
            is_code_block = False
            current_chunk = ""

            if self.streaming_output:
                # Tell client we’re in LLM mode
                nw.send_msg("llm")
                nw.receive_ack()

                # Stream partial chunks
                for chunk in ollama.generate(
                    model=self.model, prompt=prompt, stream=True
                ):
                    text_piece = chunk["response"]
                    for char in text_piece:
                        current_chunk += char
                        full_response += char

                        # Toggle code blocks if ``` found
                        if "```" in current_chunk:
                            is_code_block = not is_code_block
                            current_chunk = current_chunk.replace("```", "")

                        # Send a chunk whenever we have a sentence end or big buffer
                        if (
                            current_chunk.endswith((".", "!", "?", "`"))
                            or len(current_chunk) > 80
                        ):
                            nw.receive_ack()
                            nw.send_msg(current_chunk.strip())
                            nw.receive_ack()
                            nw.send_msg(str(is_code_block))
                            current_chunk = ""

                # Send any leftover chunk
                if current_chunk.strip():
                    nw.receive_ack()
                    nw.send_msg(current_chunk.strip())
                    nw.receive_ack()
                    nw.send_msg(str(is_code_block))

                # Finished streaming chunks, now send “streaming_end”
                nw.send_msg("streaming_end")
                nw.receive_ack()

            else:
                # Non-streaming: single response
                response = ollama.generate(
                    model=self.model, prompt=prompt, stream=False
                )
                full_response = response["response"]

                # Send final text
                nw.send_msg(full_response.strip())

            return full_response.strip()

        except Exception as e:
            print(f"Error running Ollama: {e}")
            try:
                nw.send_msg("streaming_end")
                nw.receive_ack()
            except:
                pass
            return "Sorry, I encountered an error."
