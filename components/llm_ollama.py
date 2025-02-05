import subprocess
import json


class LlmOllama:
    def __init__(self, model_name: str):
        self.model = model_name
        self.streaming_output = True

    def get_answer(self, nw, tts, prompt: str) -> str:
        # Use subprocess to call ollama
        try:
            process = subprocess.Popen(
                ["ollama", "run", self.model, prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            response = ""
            # Stream the output
            for line in process.stdout:
                response += line
                if self.streaming_output:
                    nw.send_msg(line.strip())

            return response.strip()

        except Exception as e:
            print(f"Error running Ollama: {e}")
            return "Sorry, I encountered an error."
