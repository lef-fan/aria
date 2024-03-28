import logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
import argparse
import json
import time
import threading
from copy import deepcopy
from os.path import join
from components.vad import Vad
from components.stt import Stt
from components.llm import Llm
from components.tts import Tts
from components.ap import Ap
from components.mic import Mic
from components.ui import Ui
from components.utils import remove_emojis
from components.utils import remove_multiple_dots
from components.utils import remove_code_blocks
from components.utils import find_code_blocks
# import scipy.io.wavfile as wf


def load_config(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    return json_data

def main(ui, config):
    vad_params = config.get("Vad", {}).get("params", {})
    stt_params = config.get("Stt", {}).get("params", {})
    llm_params = config.get("Llm", {}).get("params", {})
    tts_params = config.get("Tts", {}).get("params", {})
    ap_params = config.get("Ap", {}).get("params", {})
    mic_params = config.get("Mic", {}).get("params", {})
    
    ui.add_message("system", "Loading...", new_entry=False)
    print('Loading...')
    
    vad = Vad(params=vad_params)
    stt = Stt(params=stt_params)
    llm = Llm(params=llm_params)
    ap = Ap(params=ap_params, ui=ui)
    tts = Tts(params=tts_params, ap=ap)
    mic = Mic(params=mic_params, ui=ui, vad_params=vad_params)
    
    mic_muted = False
    mic_last_chunk = None
    ap.play_sound(ap.listening_sound)
    ui.load_visual("You")
    ui.add_message("system", "\nReady...", new_entry=False)
    print('Ready...\n\n🎙...', end= " ")
    mic.start_mic()
    while True:
        skip_sleep = False
        if ui.kill:
            print("\nShutting down...")
            break
        mic_chunk = mic.get_chunk()
        if len(mic_chunk) == mic.buffer_size:
            if max(mic_chunk) == 0 and not mic_muted:
                mic_muted = True
                mic.update_ui = False
                ui.load_visual("system_muted_mic")
                vad.reset_vad()
                mic.reset_recording()
                skip_sleep = True
            elif not (mic_chunk==mic_last_chunk).all() and max(mic_chunk) != 0:
                if mic_muted:
                    ui.load_visual("You")
                    mic.update_ui = True
                    mic_muted = False
                mic_last_chunk = deepcopy(mic_chunk)
                mic.vad_time = vad.no_voice_wait_sec - vad.no_voice_sec
                vad_status = vad.check(mic_chunk, mic.buffer_size / mic.samplerate)
                if vad_status is None:
                    mic.reset_recording()
                    skip_sleep = True
                elif vad_status == "vad_end":
                    mic.stop_mic()
                    ui.load_visual("system_transition")
                    ap.play_sound(ap.transition_sound)
                    mic_recording = mic.get_recording()
                    mic_recording = mic_recording[:-vad.no_voice_wait_sec*mic.samplerate]
                    # wf.write('test.wav', mic.samplerate, mic_recording)
                    stt_data = stt.transcribe_translate(mic_recording)
                    if len(stt_data) != 1:
                        ui.add_message("You", stt_data, new_entry=True)
                        print("You:", stt_data)
                        print("🤖...", end=" ")
                        llm_data = llm.get_answer(ui, ap, tts, stt_data)
                        if not llm.streaming_output:
                            print("Aria:", llm_data)
                            code_blocks = find_code_blocks(llm_data)
                            if len(code_blocks) > 0:
                                color_code_block = True
                            else:
                                color_code_block = False
                            ui.add_message("Aria", llm_data, new_entry=True, color_code_block=color_code_block, code_blocks=code_blocks)
                            tts.text_splitting = True
                            # TODO handle emphasis
                            txt_for_tts = remove_emojis(remove_multiple_dots(remove_code_blocks(llm_data)))
                            if not all(char.isspace() for char in txt_for_tts):
                                tts.run_tts(txt_for_tts)
                                ap.check_audio_finished()
                    else:
                        # TODO add to llm context
                        ui.add_message("You", "...", new_entry=True)
                        print("You: ...")
                        ui.add_message("Aria", "Did you say something?", new_entry=True)
                        print("🤖... Aria:", "Did you say something?")
                        tts.run_tts("Did you say something?")
                        ap.check_audio_finished()
                    time.sleep(1)
                    ap.play_sound(ap.listening_sound)
                    ui.load_visual("You")
                    print("\n🎙...", end=" ")
                    mic.start_mic()
                    skip_sleep = True
                else:
                    pass
            else:
                pass
        if not skip_sleep:
            time.sleep(mic.buffer_size / mic.samplerate)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aria.")
    parser.add_argument("--config", default="default.json", help="Path to JSON config file in the configs folder")
    args = parser.parse_args()
    
    config_path = join("configs", args.config)
    config = load_config(config_path)
    
    ui_params = config.get("Ui", {}).get("params", {})
    ui = Ui(params=ui_params)
    
    aria_thread = threading.Thread(target=main, args=(ui, config))
    aria_thread.start()
    
    ui.start()
