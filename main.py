import logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
import argparse
import json
import time
from os.path import join
import numpy as np
import torch
from components.mic import Mic
from components.vad import Vad
from components.stt import Stt
from components.ap import Ap


def main(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    
    mic_params = json_data.get("Mic", {}).get("params", {})
    vad_params = json_data.get("Vad", {}).get("params", {})
    stt_params = json_data.get("Stt", {}).get("params", {})
    ap_params = json_data.get("Ap", {}).get("params", {})
    
    mic = Mic(params=mic_params)
    vad = Vad(params=vad_params)
    stt = Stt(params=stt_params)
    ap = Ap(params=ap_params)
    
    final_data = torch.Tensor()
    
    ap.play(ap.listening_sound, ap.listening_sound_sr)
    while True:
        mic_data = mic.get_data()
        if mic_data is not None:
            mic_data = np.frombuffer(mic_data, np.int16).flatten().astype(np.float32) / 32768.0
            mic_data = torch.Tensor(mic_data)
            vad_data = vad.check(mic_data)
            if vad_data == None:
                pass
            elif vad_data == "vad end":
                # logging.info("vad end:")
                # logging.info(final_data)
                stt_data = stt.transcribe(final_data)[1:]
                mic.stop_mic()
                ap.play(ap.speaking_sound, ap.speaking_sound_sr)
                if len(stt_data) != 1:
                    logging.info("stt data: " + stt_data)
                    ap.play(ap.listening_sound, ap.listening_sound_sr)
                    mic.start_mic()
                final_data = torch.Tensor()
            else:
                final_data = torch.cat([final_data, mic_data])
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aria.")
    parser.add_argument("--config", default="default.json", help="Path to JSON config file in the configs folder")
    args = parser.parse_args()
    
    config_path = join("configs", args.config)
    main(config_path)
