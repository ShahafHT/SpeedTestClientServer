import socket
import struct
import threading
import time
import argparse
import selectors

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
        self.broadcast_socket.bind((self.ip, self.port + 2))
        self.tcp_socket.bind((self.ip, self.port))
        self.tcp_socket.listen(50)
        print(f"Server listening on {self.actual_ip}:{self.port} (TCP) and {self.port + 1} (UDP)")

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.tcp_socket, selectors.EVENT_READ, self.accept_tcp_connection)
        self.selector.register(self.udp_socket, selectors.EVENT_READ, self.handle_udp_client)

    def send_offers(self):
        offer_message = struct.pack('!IBHH', 0xabcddcba, 0x2, self.port + 1, self.port)
        self.broadcast_socket.sendto(offer_message, ('255.255.255.255', self.port + 2))
        print(f"Sent offer from {self.actual_ip}")
        threading.Timer(1, self.send_offers).start()

    def handle_udp_client(self, udp_socket):
        data, addr = udp_socket.recvfrom(1024)
        if not data:
            return
        print(f"Received UDP data from {addr}")
        # Unpack the request message
        magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)
        if magic_cookie != 0xabcddcba or message_type != 0x3:
            return  # Invalid request message
        # Send the requested data with sequence numbers
        total_segments = (file_size + 1019) // 1020  # Calculate total segments
        bytes_sent = 0
        sequence_number = 0
        while bytes_sent < file_size:
            chunk_size = min(1020, file_size - bytes_sent)
            packet = struct.pack('!IBQQ', 0xabcddcba, 0x4, total_segments, sequence_number) + b'0' * chunk_size
            udp_socket.sendto(packet, addr)
            bytes_sent += chunk_size
            sequence_number += 1

    def accept_tcp_connection(self, tcp_socket):
        client_socket, addr = tcp_socket.accept()
        print(f"Accepted TCP connection from {addr}")
        self.selector.register(client_socket, selectors.EVENT_READ, self.handle_tcp_client)

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
            self.selector.unregister(client_socket)
            client_socket.close()

    def start(self):
        threading.Thread(target=self.send_offers).start()
        while True:
            events = self.selector.select()
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)

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