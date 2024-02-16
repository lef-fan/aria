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
    
    mic_last_chunk = None
    ap.play_sound(ap.listening_sound, ap.listening_sound_sr)
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
            if not (mic_chunk==mic_last_chunk).all():
                mic_last_chunk = deepcopy(mic_chunk)
                ui.update_spectrum_viz("You", mic_chunk, time_color_warning=vad.no_voice_wait_sec - vad.no_voice_sec)
                vad_status = vad.check(mic_chunk, mic.buffer_size / mic.samplerate)
                if vad_status is None:
                    mic.reset_recording()
                    skip_sleep = True
                elif vad_status == "vad_end":
                    mic.stop_mic()
                    ap.play_sound(ap.speaking_sound, ap.speaking_sound_sr)
                    ui.update_spectrum_viz("system", None)
                    mic_recording = mic.get_recording()
                    mic_recording = mic_recording[:-vad.no_voice_wait_sec*mic.samplerate]
                    # wf.write('test.wav', mic.samplerate, mic_recording)
                    stt_data = stt.transcribe_translate(mic_recording)
                    if len(stt_data) != 1:
                        ui.add_message("You", stt_data, new_entry=True)
                        print("You:", stt_data)
                        print("🤖...", end=" ")
                        llm_data = llm.get_answer(ui, tts, stt_data)
                        if not llm.streaming_output:
                            print("Aria:", llm_data)
                            ui.add_message("Aria", llm_data, new_entry=True)
                            tts.text_splitting = True
                            tts_status = tts.run_tts(llm_data)
                            tts.check_last_chunk()
                    else:
                        print("You: ...")
                        ui.add_message("Aria", "Did you say something?", new_entry=True)
                        print("🤖... Aria:", "Did you say something?")
                        tts_status = tts.run_tts("Did you say something?")
                        tts.check_last_chunk()
                    time.sleep(1)
                    ap.play_sound(ap.listening_sound, ap.listening_sound_sr)
                    print("\n🎙...", end=" ")
                    mic.start_mic()
                    skip_sleep = True
                else:
                    # logging.info("respond starts in: " + str(vad.no_voice_wait_sec - vad.no_voice_sec))
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
