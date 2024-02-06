import logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
import argparse
import json
import time
from copy import deepcopy
from os.path import join
import numpy as np
from components.vad import Vad
from components.stt import Stt
from components.llm import Llm
from components.ap import Ap
from components.mic import Mic


def main(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    
    vad_params = json_data.get("Vad", {}).get("params", {})
    stt_params = json_data.get("Stt", {}).get("params", {})
    llm_params = json_data.get("Llm", {}).get("params", {})
    ap_params = json_data.get("Ap", {}).get("params", {})
    mic_params = json_data.get("Mic", {}).get("params", {})
    
    vad = Vad(params=vad_params)
    stt = Stt(params=stt_params)
    llm = Llm(params=llm_params)
    ap = Ap(params=ap_params)
    mic = Mic(params=mic_params)
    
    final_data = None
    
    time.sleep(1)
    ap.play(ap.listening_sound, ap.listening_sound_sr)
    mic.start_mic()
    while True:
        mic_data = mic.get_data()
        if mic_data is not None:
            vad_data = vad.check(mic_data)
            if vad_data is None:
                pass
            elif vad_data == "vad end":
                # logging.info("vad end:")
                # logging.info(final_data)
                stt_data = stt.transcribe_translate(final_data)
                mic.stop_mic()
                ap.play(ap.speaking_sound, ap.speaking_sound_sr)
                if len(stt_data) != 1:
                    logging.info("user: " + stt_data)
                    llm_data = llm.get_answer(stt_data)
                    logging.info("aria: " + llm_data)
                time.sleep(1)
                ap.play(ap.listening_sound, ap.listening_sound_sr)
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
    main(config_path)
