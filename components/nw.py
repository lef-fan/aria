import socket


class Nw:
    def __init__(self, params=None):
        self.params = params or {}
        self.host_ip = self.params.get('host_ip', None)
        self.client_target_ip = self.params.get('client_target_ip', None)
        self.port = self.params.get('port', None)
        
    def server_init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host_ip, self.port))
        self.server_socket.listen(0)
        
    def server_listening(self):
        con, client_address = self.server_socket.accept()
        con.sendall(b'ACK')
        return con, client_address
        
    def client_init(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def client_connect(self):
        self.client_socket.connect((self.client_target_ip, self.port))
        ack = self.client_socket.recv(1024)
        return self.client_socket
