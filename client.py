import argparse
import json
import time
import threading
from copy import deepcopy
from os.path import join
import numpy as np
import socket
from components.nw import Nw
from components.ap import Ap
from components.mic import Mic
from components.ui import Ui
from components.utils import find_code_blocks
# import scipy.io.wavfile as wf


def load_config(config_file):
    with open(config_file, "r") as file:
        json_data = json.load(file)
    return json_data

def main(nw, ui, mic, ap, vad_params, llm_params):
    nw.client_init()
    ui.add_message("system", "Connecting...", new_entry=False)
    print('Connecting...')
    while True:
        try:
            nw.client_connect()
            break
        except:
            time.sleep(1)
    ui.add_message("system", "\nConnected!", new_entry=False)
    print("Connected!")
    
    ap.play_sound(ap.listening_sound)
    ui.load_visual("You")
    
    mic_muted = False
    mic_last_chunk = None
    mic.start_mic()
    
    while True:
        skip_sleep = False
        if ui.kill:
            print("Shutting down...")
            break
        mic_chunk = mic.get_chunk()
        if len(mic_chunk) == mic.buffer_size:
            if max(mic_chunk) == 0 and not mic_muted:
                mic_muted = True
                mic.update_ui = False
                ui.load_visual("system_muted_mic")
                nw.send_msg("reset_vad")
                nw.receive_ack()
                mic.reset_recording()
                skip_sleep = True
            elif not (mic_chunk==mic_last_chunk).all() and max(mic_chunk) != 0:
                if mic_muted:
                    ui.load_visual("You")
                    mic.update_ui = True
                    mic_muted = False
                mic_last_chunk = deepcopy(mic_chunk)
                nw.send_msg("vad_time")
                vad_time = nw.receive_msg()
                mic.vad_time = float(vad_time)
                nw.send_msg("vad_check")
                nw.receive_ack()
                nw.send_audio(mic_chunk.tobytes())
                vad_status = nw.receive_msg()
                if vad_status == 'None':
                    mic.reset_recording()
                    skip_sleep = True
                elif vad_status == "vad_end":
                    mic.stop_mic()
                    ui.load_visual("system_transition")
                    ap.play_sound(ap.transition_sound)
                    mic_recording = mic.get_recording()
                    vad_no_voice_wait_sec = vad_params.get('no_voice_wait_sec', None)
                    mic_recording = mic_recording[:-vad_no_voice_wait_sec*mic.samplerate]
                    # wf.write('test.wav', mic.samplerate, mic_recording)
                    nw.send_msg("stt_transcribe")
                    nw.receive_ack()
                    nw.send_msg(str(len(mic_recording.tobytes())))
                    nw.receive_ack()
                    nw.send_audio(mic_recording.tobytes())
                    stt_data = nw.receive_msg()
                    if len(stt_data) != 1:
                        ui.add_message("You", stt_data, new_entry=True)
                        nw.send_msg("llm_get_answer")
                        if not llm_params.get('streaming_output', None):
                            llm_data_size = nw.receive_msg()
                            nw.send_ack()
                            llm_data = nw.receive_msg(int(llm_data_size), waitall=True)
                            code_blocks = find_code_blocks(llm_data)
                            if len(code_blocks) > 0:
                                color_code_block = True
                            else:
                                color_code_block = False
                            ui.add_message("Aria", llm_data, new_entry=True, color_code_block=color_code_block, code_blocks=code_blocks)
                            while True:
                                nw.send_ack()
                                tts_chunk_size = nw.receive_msg()
                                if tts_chunk_size == "tts_end":
                                    break
                                else:
                                    nw.send_ack()
                                    tts_chunk = nw.receive_audio(int(tts_chunk_size))
                                    ap.stream_sound(np.frombuffer(tts_chunk, np.float32).flatten(), update_ui=True)
                            ap.check_audio_finished()
                        else:
                            nw.receive_ack()
                            ui.add_message("Aria", "", new_entry=True)
                            while True:
                                nw.send_ack()
                                llm_or_tts = nw.receive_msg()
                                if llm_or_tts == "llm":
                                    nw.send_ack()
                                    llm_chunk_size = nw.receive_msg()
                                    nw.send_ack()
                                    llm_chunk = nw.receive_msg(int(llm_chunk_size), waitall=True)
                                    nw.send_ack()
                                    color_code_block = nw.receive_msg()
                                    ui.add_message("Aria", llm_chunk, new_entry=False, color_code_block=color_code_block.lower()=='true')
                                elif llm_or_tts == "tts":
                                    while True:
                                        nw.send_ack()
                                        tts_chunk_size = nw.receive_msg()
                                        if tts_chunk_size == "tts_end":
                                            break
                                        else:
                                            nw.send_ack()
                                            tts_chunk = nw.receive_audio(int(tts_chunk_size))
                                            ap.stream_sound(np.frombuffer(tts_chunk, np.float32).flatten(), update_ui=True)
                                elif llm_or_tts == "streaming_end":
                                    break
                            ap.check_audio_finished()
                    else:
                        # TODO add to llm context
                        ui.add_message("You", "...", new_entry=True)
                        nw.send_msg("fixed_answer")
                        ui.add_message("Aria", "Did you say something?", new_entry=True)
                        while True:
                            nw.send_ack()
                            tts_chunk_size = nw.receive_msg()
                            if tts_chunk_size == "tts_end":
                                break
                            else:
                                nw.send_ack()
                                tts_chunk = nw.receive_audio(int(tts_chunk_size))
                                ap.stream_sound(np.frombuffer(tts_chunk, np.float32).flatten(), update_ui=True)
                        ap.check_audio_finished()
                    time.sleep(1)
                    ap.play_sound(ap.listening_sound)
                    ui.load_visual("You")
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
    
    nw_params = config.get("Nw", {}).get("params", {})
    ap_params = config.get("Ap", {}).get("params", {})
    mic_params = config.get("Mic", {}).get("params", {})
    ui_params = config.get("Ui", {}).get("params", {})
    vad_params = config.get("Vad", {}).get("params", {})
    llm_params = config.get("Llm", {}).get("params", {})
    
    nw = Nw(params=nw_params)
    ui = Ui(params=ui_params)
    ap = Ap(params=ap_params, ui=ui)
    mic = Mic(params=mic_params, ui=ui, vad_params=vad_params)
    
    com_thread = threading.Thread(target=main, args=(nw, ui, mic, ap, vad_params, llm_params))
    com_thread.start()
    
    ui.start()
