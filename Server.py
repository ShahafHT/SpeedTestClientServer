import socket
import struct
import threading
import time
import argparse

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
            offer_message = struct.pack('!IBHH', 0xabcddcba, 0x2, self.port + 1, self.port)
            self.broadcast_socket.sendto(offer_message, ('255.255.255.255', self.port + 2))
            print(f"Sent offer from {self.actual_ip}")
            time.sleep(1)

    def handle_udp_client(self):
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            if not data:
                break
            print(f"Received UDP data from {addr}: {data}")
            # Unpack the request message
            magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)
            if magic_cookie != 0xabcddcba or message_type != 0x3:
                continue  # Invalid request message
            # Send the requested data with sequence numbers
            total_segments = (file_size + 1019) // 1020  # Calculate total segments
            bytes_sent = 0
            sequence_number = 0
            while bytes_sent < file_size:
                chunk_size = min(1020, file_size - bytes_sent)
                packet = struct.pack('!IBQQ', 0xabcddcba, 0x4, total_segments, sequence_number) + b'0' * chunk_size
                self.udp_socket.sendto(packet, addr)
                bytes_sent += chunk_size
                sequence_number += 1

    def handle_tcp_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode().strip()
            if not data:
                return
            print(f"Received TCP data: {data}")
            # Parse the requested file size
            file_size = int(data)
            # Send the requested data as a single chunk
            client_socket.sendall(b'0' * file_size)
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

def main():
    parser = argparse.ArgumentParser(description="Network Speed Test Server")
    parser.add_argument('--host', default='0.0.0.0', help="Server IP address")
    parser.add_argument('--port', type=int, default=5001, help="Server port")
    args = parser.parse_args()

    print(f"Starting server on {args.host}:{args.port}")
    server = SpeedTestServer(ip=args.host, port=args.port)
    server.start()

if __name__ == "__main__":
    main()