import socket
import threading
import time
import struct

# Server class to handle incoming connections and speed test requests
class SpeedTestServer:
    def __init__(self, host='0.0.0.0', port=5001):
        self.host = host
        self.port = port
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Set SO_REUSEADDR option for UDP socket
        self.udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.tcp_server.bind((self.host, self.port))
        self.udp_server.bind((self.host, self.port + 1))
        self.tcp_server.listen(5)
        print(f"TCP server listening on {self.host}:{self.port}")
        print(f"UDP server listening on {self.host}:{self.port + 1}")

    # Method to handle TCP connections
    def handle_tcp_client(self, client_socket):
        print("TCP client connected.")
        try:
            while True:
                # Receive data from the client
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received TCP data: {data}")
                # Simulate sending back a speed test response
                time.sleep(0.1)  # Simulate processing delay
                client_socket.sendall(data)  # Echo back the received data
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()
            print("TCP client disconnected.")

    # Method to handle UDP connections
    def handle_udp_client(self):
        print("UDP server ready to receive data.")
        while True:
            try:
                data, addr = self.udp_server.recvfrom(1024)
                print(f"Received UDP data from {addr}: {data}")
                # Simulate sending back a speed test response
                time.sleep(0.1)  # Simulate processing delay
                self.udp_server.sendto(data, addr)  # Echo back the received data
            except Exception as e:
                print(f"Error: {e}")

    # Method to start the server
    def start(self):
        tcp_thread = threading.Thread(target=self.tcp_server_loop)
        udp_thread = threading.Thread(target=self.handle_udp_client)
        tcp_thread.start()
        udp_thread.start()
        tcp_thread.join()
        udp_thread.join()

    # TCP server loop to accept connections
    def tcp_server_loop(self):
        while True:
            try:
                client_socket, addr = self.tcp_server.accept()
                print(f"Accepted TCP connection from {addr}.")
                client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,))
                client_thread.start()
            except Exception as e:
                print(f"Error: {e}")