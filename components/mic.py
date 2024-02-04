from copy import deepcopy
import pyaudio


class Mic:
    """
    Represents a microphone component.

    Args:
        params (dict): Optional parameters for the microphone.
            - samplerate (int): The sample rate of the microphone.
            - buffer_size (int): The buffer size of the microphone.
            - channels (int): The number of channels of the microphone.

    Attributes:
        samplerate (int): The sample rate of the microphone.
        buffer_size (int): The buffer size of the microphone.
        channels (int): The number of channels of the microphone.
        sample_format: The sample format of the microphone.
        p: The PyAudio instance.
        stream: The audio stream.
        data: The audio data captured by the microphone.

    """

    def __init__(self, params=None):
        self.params = params or {}
        self.samplerate = self.params.get('samplerate', None)
        self.buffer_size = self.params.get('buffer_size', None)
        self.channels = self.params.get('channels', None)
        self.device = self.params.get('device', None)
        self.sample_format = pyaudio.paInt16
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.samplerate,
            frames_per_buffer=self.buffer_size,
            input=True,
            input_device_index=self.device,
            stream_callback=self._update_data,
        )
        
        self.data = None

    def _update_data(self, in_data, frame_count, time_info, status):
        """
        Callback function to update the audio data.

        Args:
            in_data: The input audio data.
            frame_count: The number of frames in the input data.
            time_info: Time information of the input data.
            status: Status information of the input data.

        Returns:
            tuple: A tuple containing the updated audio data and the status to continue the stream.

        """
        self.data = deepcopy(in_data)
        return (in_data, pyaudio.paContinue)

    def get_data(self):
        """
        Get the captured audio data.

        Returns:
            The captured audio data.

        """
        return self.data
    
    def start_mic(self):
        """
        Start the microphone stream.

        """
        self.stream.start_stream()
    
    def stop_mic(self):
        """
        Stop the microphone stream.

        """
        self.stream.stop_stream()
