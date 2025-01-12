import socket
import threading
import struct
import time

class SpeedTestClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set SO_REUSEADDR option for UDP socket
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def send_udp_request(self, file_size):
        try:
            # Create request message
            magic_cookie = 0xabcddcba
            message_type = 0x3
            request_message = struct.pack('!IBQ', magic_cookie, message_type, file_size)
            self.udp_socket.sendto(request_message, (self.server_ip, self.server_port + 1))
            print(f"Sent UDP request to {self.server_ip}:{self.server_port + 1}")
            
            # Receive payload
            while True:
                data, addr = self.udp_socket.recvfrom(1024)
                if not data:
                    break
                print(f"Received UDP data from {addr}: {data}")
        except Exception as e:
            print(f"Error: {e}")

    def send_tcp_request(self, file_size):
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            print(f"Connected to TCP server at {self.server_ip}:{self.server_port}")
            self.tcp_socket.sendall(f"{file_size}\n".encode())
            
            # Receive file
            while True:
                data = self.tcp_socket.recv(1024)
                if not data:
                    break
                print(f"Received TCP data: {data}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.tcp_socket.close()

    def start(self):
        file_size = int(input("Enter the file size for the speed test: "))
        udp_thread = threading.Thread(target=self.send_udp_request, args=(file_size,))
        tcp_thread = threading.Thread(target=self.send_tcp_request, args=(file_size,))
        udp_thread.start()
        tcp_thread.start()
        udp_thread.join()
        tcp_thread.join()