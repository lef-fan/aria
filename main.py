import logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
import argparse
import json
import time
import threading
from copy import deepcopy
from os.path import join
import numpy as np
from components.vad import Vad
from components.stt import Stt
from components.llm import Llm
from components.tts import Tts
from components.ap import Ap
from components.mic import Mic
from components.ui import Ui
from components.utils import remove_emojis
from components.utils import remove_multiple_dots
from components.utils import remove_inside_backticks
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
    tts = Tts(params=tts_params)
    ap = Ap(params=ap_params)
    mic = Mic(params=mic_params)
    
    mic_last_data = None
    final_data = np.empty(mic.buffer_size)
    
    time.sleep(1)
    ap.play_sound(ap.listening_sound, ap.listening_sound_sr)
    ui.add_message("system", "\nReady...", new_entry=False)
    print('Ready...')
    mic.start_mic()
    while True:
        if ui.kill:
            break
        mic_data = mic.get_data()
        if mic_data is not None:
            if not (mic_data==mic_last_data).all():
                mic_last_data = deepcopy(mic_data)
                vad_data = vad.check(mic_data)
                if vad_data is None:
                    pass
                elif vad_data == "vad end":
                    # logging.info("vad end:")
                    # logging.info(final_data)
                    # wf.write('test.wav', mic.samplerate, final_data)
                    stt_data = stt.transcribe_translate(final_data)
                    mic.stop_mic()
                    ap.play_sound(ap.speaking_sound, ap.speaking_sound_sr)
                    if len(stt_data) != 1:
                        ui.add_message("user", stt_data, new_entry=True)
                        print("user:", stt_data) 
                        llm_data = llm.get_answer(stt_data, ui)
                        if not llm.streaming_output:
                            ui.add_message("aria", llm_data, new_entry=True)
                            print("aria:", llm_data)
                        tts_status = tts.run_tts(remove_emojis(remove_multiple_dots(remove_inside_backticks(llm_data))))
                    else:
                        ui.add_message("aria", "Did you say something?", new_entry=True)
                        print("aria:", "Did you say something?")
                        tts_status = tts.run_tts("Did you say something?")
                    time.sleep(1)
                    ap.play_sound(ap.listening_sound, ap.listening_sound_sr)
                    mic.start_mic()
                    final_data = None
                    continue
                else:
                    if final_data is None:
                        final_data = deepcopy(mic_data)
                    else:
                        final_data = np.concatenate([final_data, mic_data])
                    # logging.info("respond starts in: " + str(vad.no_voice_wait_sec - vad.no_voice_sec))
        time.sleep(1)

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
