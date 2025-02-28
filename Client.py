import socket
import threading
import struct
import time
import argparse
import selectors

class SpeedTestClient:
    def __init__(self, listen_port=5003):  # Default to self.port + 2
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', listen_port - 1))  # Bind to the port used for receiving offers

        # Enable broadcast on the broadcast socket
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.bind(('', listen_port))  # Bind to the port used for sending offers

        self.selector = selectors.DefaultSelector()
        self.selector.register(self.broadcast_socket, selectors.EVENT_READ, self.handle_offer)

        self.file_size = int(input("Enter the file size for the speed test (in bytes): "))
        self.tcp_connections = int(input("Enter the number of TCP connections: "))
        self.udp_connections = int(input("Enter the number of UDP connections: "))

    def handle_offer(self, broadcast_socket):
        try:
            data, addr = broadcast_socket.recvfrom(2048)  # Increase buffer size to 2048 bytes
            magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])
            if magic_cookie == 0xabcddcba and message_type == 0x2:
                print(f"Received offer from {addr[0]}: UDP port {udp_port}, TCP port {tcp_port}")
                self.server_ip = addr[0]
                self.udp_port = udp_port
                self.tcp_port = tcp_port
                self.selector.unregister(broadcast_socket)
                self.start_transfers()
        except Exception as e:
            print(f"Error receiving offer: {e}")

    def send_udp_request(self, server_ip, udp_port, file_size, udp_index):
        try:
            # Create request message
            magic_cookie = 0xabcddcba
            message_type = 0x3
            request_message = struct.pack('!IBQ', magic_cookie, message_type, file_size)
            self.udp_socket.sendto(request_message, (server_ip, udp_port))

            start_time = time.time()
            bytes_received = 0
            last_packet_time = time.time()

            # Receive payload
            while bytes_received < file_size:
                self.udp_socket.settimeout(1)
                try:
                    data, addr = self.udp_socket.recvfrom(2048)  # Increase buffer size to 2048 bytes
                    if not data:
                        break
                    magic_cookie, message_type, total_segments, current_segment = struct.unpack('!IBQQ', data[:21])
                    if magic_cookie != 0xabcddcba or message_type != 0x4:
                        continue  # Invalid payload message
                    payload = data[21:]
                    bytes_received += len(payload)  # Use the length of the payload directly
                    last_packet_time = time.time()
                except socket.timeout:
                    if time.time() - last_packet_time > 1:
                        print(f"UDP transfer #{udp_index} timed out, closing connection")
                        return

            end_time = time.time()
            total_time = end_time - start_time
            speed = (bytes_received * 8) / total_time
            packets_received_percentage = (bytes_received / file_size) * 100 if file_size > 0 else 0

            if packets_received_percentage > 100:
                packets_received_percentage = 100

            print(f"UDP transfer #{udp_index} finished, total time: {total_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {packets_received_percentage:.2f}%")
        except Exception as e:
            print(f"Error: {e}")

    def send_tcp_request(self, server_ip, tcp_port, file_size, tcp_index):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((server_ip, tcp_port))
            # Create request message
            request_message = f"{file_size}\n".encode()
            tcp_socket.sendall(request_message)
            
            start_time = time.time()
            bytes_received = 0

            # Receive file
            while bytes_received < file_size:
                data = tcp_socket.recv(1024)
                if not data:
                    break
                bytes_received += len(data)

            end_time = time.time()
            total_time = end_time - start_time
            speed = (bytes_received * 8) / total_time

            print(f"TCP transfer #{tcp_index} finished, total time: {total_time:.2f} seconds, total speed: {speed:.2f} bits/second")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            tcp_socket.close()

    def start_transfers(self):
        threads = []

        for i in range(self.tcp_connections):
            tcp_thread = threading.Thread(target=self.send_tcp_request, 
                                       args=(self.server_ip, self.tcp_port, self.file_size, i + 1))
            threads.append(tcp_thread)
            tcp_thread.start()

        for i in range(self.udp_connections):
            udp_thread = threading.Thread(target=self.send_udp_request, 
                                       args=(self.server_ip, self.udp_port, self.file_size, i + 1))
            threads.append(udp_thread)
            udp_thread.start()

        for thread in threads:
            thread.join()

        print("\nAll transfers complete, listening to offer requests\n")
        self.selector.register(self.broadcast_socket, selectors.EVENT_READ, self.handle_offer)

    def start(self):
        print("Client started, listening for offer requests...")
        while True:
            events = self.selector.select()
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)

def main():
    parser = argparse.ArgumentParser(description="Network Speed Test Client")
    parser.add_argument('--listen_port', type=int, default=5003, help="Client listen port for offers")
    args = parser.parse_args()

    client = SpeedTestClient(listen_port=args.listen_port)
    client.start()

if __name__ == "__main__":
    main()