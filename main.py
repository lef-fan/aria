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


def main(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    
    mic_params = json_data.get("Mic", {}).get("params", {})
    vad_params = json_data.get("Vad", {}).get("params", {})
    
    mic = Mic(params=mic_params)
    vad = Vad(params=vad_params)
    
    final_data = torch.Tensor()
    
    while True:
        data = mic.get_data()
        if data is not None:
            data = np.frombuffer(data, np.int16).flatten().astype(np.float32) / 32768.0
            data = torch.Tensor(data)
            data = vad.check_data(data)
            if data == None:
                pass
            elif data == "vad end":
                logging.info("vad end:")
                logging.info(final_data)
                final_data = torch.Tensor()
            else:
                final_data = torch.cat([final_data, data])
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aria.")
    parser.add_argument("--config", default="default.json", help="Path to JSON config file in the configs folder")
    args = parser.parse_args()
    
    config_path = join("configs", args.config)
    main(config_path)
