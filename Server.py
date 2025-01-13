import socket
import struct
import threading
import time

class SpeedTestServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.actual_ip = socket.gethostbyname(socket.gethostname())  # Get the actual IP address of the server
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind((self.ip, self.port + 1))
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.tcp_socket.bind((self.ip, self.port))
        self.tcp_socket.listen(5)
        print(f"Server listening on {self.actual_ip}:{self.port} (TCP) and {self.port + 1} (UDP)")

    def send_offers(self):
        while True:
            offer_message = struct.pack('!IB', 0xabcddcba, 0x2)
            self.broadcast_socket.sendto(offer_message, ('<broadcast>', self.port + 2))
            print(f"Sent offer from {self.actual_ip}")
            time.sleep(1)

    def handle_udp_client(self):
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            if not data:
                break
            print(f"Received UDP data from {addr}: {data}")
            # Simulate sending the requested data
            for i in range(10):
                self.udp_socket.sendto(b'0' * 1024, addr)
                time.sleep(0.1)

    def handle_tcp_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received TCP data: {data}")
                # Simulate sending the requested data
                for i in range(10):
                    client_socket.sendall(b'0' * 1024)
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def start(self):
        udp_thread = threading.Thread(target=self.handle_udp_client)
        udp_thread.start()

        offer_thread = threading.Thread(target=self.send_offers)
        offer_thread.start()

        while True:
            client_socket, addr = self.tcp_socket.accept()
            print(f"Accepted TCP connection from {addr}")
            tcp_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,))
            tcp_thread.start()