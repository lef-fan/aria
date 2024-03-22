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
    print("Server listening...")
    con, client_address = nw.server_listening()
    print("Client connected:", client_address)
    
    while True:    
        client_data = con.recv(1024)
        if not client_data:
            print("Server listening...")
            con, client_address = nw.server_listening()
            print("Client connected:", client_address)
        if client_data == b'reset_vad':
            vad.reset_vad()
            con.sendall(b'ACK')
        elif client_data == b'vad_time':
            vad_time = vad.no_voice_wait_sec - vad.no_voice_sec
            con.sendall(str(vad_time).encode())
        elif client_data == b'vad_check':
            con.sendall(b'ACK')
            mic_chunk = con.recv(mic_params.get('buffer_size', None)*4, socket.MSG_WAITALL)
            chunk_time = mic_params.get('buffer_size', None) / mic_params.get('samplerate', None)
            vad_status = vad.check(np.frombuffer(mic_chunk, np.float32).flatten(), chunk_time)
            con.sendall(str(vad_status).encode())
        elif client_data == b'stt_transcribe':
            con.sendall(b'ACK')
            mic_recording_size = con.recv(1024).decode()
            con.sendall(b'ACK')
            mic_recording = con.recv(int(mic_recording_size), socket.MSG_WAITALL)
            # wf.write('test.wav', mic_params.get('samplerate', None), np.frombuffer(mic_recording, np.float32).flatten())
            stt_data = stt.transcribe_translate(np.frombuffer(mic_recording, np.float32).flatten())
            con.sendall(stt_data.encode())
        elif client_data == b'llm_get_answer':
            llm_data = llm.get_answer(con, tts, stt_data)
            if not llm.streaming_output:
                con.sendall(str(len(llm_data.encode())).encode())
                ack = con.recv(1024)
                con.sendall(llm_data.encode())
                tts.text_splitting = True
                # TODO handle emphasis
                tts.run_tts(con, remove_emojis(remove_multiple_dots(remove_code_blocks(llm_data))))
        elif client_data == b'fixed_answer':
            tts.run_tts(con, "Did you say something?")
