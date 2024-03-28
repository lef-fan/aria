import socket


class Nw:
    def __init__(self, params=None):
        self.params = params or {}
        self.host_ip = self.params.get('host_ip', None)
        self.port = self.params.get('port', None)
        self.client_target_ip = self.params.get('client_target_ip', None)
        self.client_target_port = self.params.get('client_target_port', None)
        self.con = None
        
    def server_init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    
    def client_connect(self):
        self.con.connect((self.client_target_ip, self.client_target_port))
        self.receive_ack()
        
    def send_ack(self):
        self.con.sendall('ACK'.encode()) 

    def send_msg(self, msg):
        self.con.sendall(msg.encode())
        
    def send_audio(self, data):
        self.con.sendall(data)
        
    def receive_ack(self):
        ack = self.con.recv(1024)
        
    def receive_msg(self, n_bytes=1024, waitall=False):
        if waitall:
            msg = self.con.recv(n_bytes, socket.MSG_WAITALL).decode()
        else:
            msg = self.con.recv(n_bytes).decode()
        return msg
    
    def receive_audio(self, n_bytes):
        data = self.con.recv(n_bytes, socket.MSG_WAITALL)
        return data
    