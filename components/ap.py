import sounddevice as sd
import soundfile as sf


class Ap:
    def __init__(self, params=None):
        self.params = params or {}
        self.listening_sound_path = self.params.get('assets', None).get('listening_sound', None)
        self.listening_sound, self.listening_sound_sr = sf.read(self.listening_sound_path)
        self.speaking_sound_path = self.params.get('assets', None).get('speaking_sound', None)
        self.speaking_sound, self.speaking_sound_sr = sf.read(self.speaking_sound_path)
        
    def play(self, sound, sr):
        sd.play(sound, sr)
        sd.wait()
