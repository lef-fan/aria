import logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
import argparse
import json
from os.path import join
import socket
import numpy as np
from components.nw import Nw
from components.vad import Vad
from components.stt import Stt
from components.llm_server import Llm
from components.tts_server import Tts
from components.utils import remove_emojis
from components.utils import remove_multiple_dots
from components.utils import remove_code_blocks
# import scipy.io.wavfile as wf


def load_config(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    return json_data
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aria.")
    parser.add_argument("--config", default="default.json", help="Path to JSON config file in the configs folder")
    args = parser.parse_args()
    
    config_path = join("configs", args.config)
    config = load_config(config_path)
    
    nw_params = config.get("Nw", {}).get("params", {})
    vad_params = config.get("Vad", {}).get("params", {})
    stt_params = config.get("Stt", {}).get("params", {})
    llm_params = config.get("Llm", {}).get("params", {})
    tts_params = config.get("Tts", {}).get("params", {})
    mic_params = config.get("Mic", {}).get("params", {})
    
    print('Loading...')
    
    nw = Nw(params=nw_params)
    vad = Vad(params=vad_params)
    stt = Stt(params=stt_params)
    llm = Llm(params=llm_params)
    tts = Tts(params=tts_params)
    
    nw.server_init()
    client_address = nw.server_listening()
    
    while True:    
        client_data = nw.receive_msg()
        if not client_data:
            print("Client disconnected...")
            client_address = nw.server_listening()
        if client_data == 'reset_vad':
            vad.reset_vad()
            nw.send_ack()
        elif client_data == 'vad_time':
            vad_time = vad.no_voice_wait_sec - vad.no_voice_sec
            nw.send_msg(str(vad_time))
        elif client_data == 'vad_check':
            nw.send_ack()
            mic_chunk = nw.receive_audio(mic_params.get('buffer_size', None)*4)
            chunk_time = mic_params.get('buffer_size', None) / mic_params.get('samplerate', None)
            vad_status = vad.check(np.frombuffer(mic_chunk, np.float32).flatten(), chunk_time)
            nw.send_msg(str(vad_status))
        elif client_data == 'stt_transcribe':
            nw.send_ack()
            mic_recording_size = nw.receive_msg()
            nw.send_ack()
            mic_recording = nw.receive_audio(int(mic_recording_size))
            # wf.write('test.wav', mic_params.get('samplerate', None), np.frombuffer(mic_recording, np.float32).flatten())
            stt_data = stt.transcribe_translate(np.frombuffer(mic_recording, np.float32).flatten())
            nw.send_msg(stt_data)
        elif client_data == 'llm_get_answer':
            llm_data = llm.get_answer(nw, tts, stt_data)
            if not llm.streaming_output:
                nw.send_msg(str(len(llm_data.encode())))
                nw.receive_ack()
                nw.send_msg(llm_data)
                tts.text_splitting = True
                # TODO handle emphasis
                txt_for_tts = remove_emojis(remove_multiple_dots(remove_code_blocks(llm_data)))
                tts.run_tts(nw, txt_for_tts)
        elif client_data == 'fixed_answer':
            tts.run_tts(nw, "Did you say something?")
