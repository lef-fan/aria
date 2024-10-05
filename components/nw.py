# import re
import struct
import socket
import opuslib


class Nw:
    def __init__(self, params=None):
        self.params = params or {}
        self.host_ip = self.params.get("host_ip", None)
        self.port = self.params.get("port", None)
        self.client_target_ip = self.params.get("client_target_ip", None)
        self.client_target_port = self.params.get("client_target_port", None)
        self.audio_compression = self.params.get("audio_compression", None)
        self.con = None
        self.buffer = bytearray()
        self.data_remaining = bytearray()

    def server_init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_socket.bind((self.host_ip, self.port))
        self.server_socket.listen(0)

    def server_listening(self):
        print("Server listening...")
        self.con, client_address = self.server_socket.accept()
        self.send_ack()
        print("Client connected:", client_address)
        return client_address

    def client_init(self):
        self.con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.con.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def client_connect(self):
        self.con.connect((self.client_target_ip, self.client_target_port))
        self.receive_ack()

    def init_audio_encoder(self, samplerate, channels, frame_size):
        self.encoder_frame_size = frame_size
        self.encoder = opuslib.Encoder(samplerate, channels, opuslib.APPLICATION_VOIP)
        # self.encoder._set_bitrate(96000)

    def init_audio_decoder(self, samplerate, channels, frame_size):
        self.decoder_frame_size = frame_size
        self.decoder = opuslib.Decoder(samplerate, channels)

    def send_ack(self):
        self.con.sendall("A".encode())

    # def send_msg(self, msg, fixed_length=0):
    #     if fixed_length > 0:
    #         msg = msg + "@" * (fixed_length - len(msg))
    #     self.con.sendall(msg.encode())
    def send_msg(self, msg):
        if isinstance(msg, int):
            # msg = struct.pack('!I', 0) + struct.pack('!I', msg)
            msg = struct.pack("!II", 0, msg)
        elif isinstance(msg, float):
            # msg = struct.pack('!I', 1) + struct.pack('!f', msg)
            msg = struct.pack("!If", 1, msg)
        elif isinstance(msg, str):
            msg_bytes = msg.encode()
            # msg = struct.pack('!I', 2) + struct.pack('!I', len(msg_bytes)) + msg_bytes
            msg = struct.pack("!II", 2, len(msg_bytes)) + msg_bytes
        self.con.sendall(msg)

    def send_audio_chunk(self, data):
        if self.audio_compression:
            data = self.encoder.encode(data, self.encoder_frame_size)
            encoded_data_size = len(data)
            self.send_msg(encoded_data_size)
        self.con.sendall(data)

    def send_audio_recording(self, data):
        if self.audio_compression:
            if len(self.data_remaining) > 0:
                self.buffer.extend(self.data_remaining)
            self.buffer.extend(data)
            remaining = len(self.buffer) % (self.encoder_frame_size * 2)
            if remaining > 0:
                self.data_remaining = self.buffer[-remaining:]
                data = bytes(self.buffer[:-remaining])
            else:
                self.data_remaining = bytearray()
                data = bytes(self.buffer)
            self.buffer = bytearray()
            for index in range(0, len(data), self.encoder_frame_size * 2):
                encoded_chunk = self.encoder.encode(
                    data[index : index + self.encoder_frame_size * 2],
                    self.encoder_frame_size,
                )
                encoded_chunk_size = len(encoded_chunk)
                self.send_msg(encoded_chunk_size)
                self.con.sendall(encoded_chunk)
            self.send_msg("audio_transmit_done")
        else:
            self.send_msg(len(data))
            self.con.sendall(data)

    def receive_ack(self):
        ack = self.con.recv(1, socket.MSG_WAITALL)

    # def receive_msg(self, n_bytes=1024, waitall=False):
    #     msg = self.con.recv(n_bytes, socket.MSG_WAITALL).decode()
    #     if not waitall:
    #         msg = re.sub(r'(\w+)@+', r'\1', msg)
    #     return msg
    def receive_msg(self):
        type_indicator = self.con.recv(4, socket.MSG_WAITALL)
        type_indicator = struct.unpack("!I", type_indicator)[0]

        if type_indicator == 0:
            msg_bytes = self.con.recv(4, socket.MSG_WAITALL)
            msg = struct.unpack("!I", msg_bytes)[0]
        elif type_indicator == 1:
            msg_bytes = self.con.recv(4, socket.MSG_WAITALL)
            msg = struct.unpack("!f", msg_bytes)[0]
        elif type_indicator == 2:
            msg_length_bytes = self.con.recv(4, socket.MSG_WAITALL)
            msg_length = struct.unpack("!I", msg_length_bytes)[0]
            msg_bytes = self.con.recv(msg_length, socket.MSG_WAITALL)
            msg = msg_bytes.decode()

        return msg

    def receive_audio_chunk(self, n_bytes):
        if self.audio_compression:
            encoded_data_size = self.receive_msg()
            encoded_data = self.con.recv(encoded_data_size, socket.MSG_WAITALL)
            data = self.decoder.decode(encoded_data, self.decoder_frame_size)
        else:
            data = self.con.recv(n_bytes, socket.MSG_WAITALL)
        return data

    def receive_audio_recording(self):
        if self.audio_compression:
            data = bytearray()
            while True:
                encoded_data_size = self.receive_msg()
                if encoded_data_size == "audio_transmit_done":
                    break
                # print("bitrate:", (encoded_data_size * 8) / (960 / 24000))
                encoded_recording = self.con.recv(encoded_data_size, socket.MSG_WAITALL)
                decoded_data = self.decoder.decode(
                    encoded_recording, self.decoder_frame_size
                )
                data.extend(decoded_data)
        else:
            encoded_data_size = self.receive_msg()
            data = self.con.recv(encoded_data_size, socket.MSG_WAITALL)
        return data
