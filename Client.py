import socket
import threading
import struct
import time
import argparse

class SpeedTestClient:
    def __init__(self, listen_port=5003):  # Default to self.port + 2
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Set SO_REUSEPORT option for UDP socket
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', listen_port))  # Bind to the port used for receiving offers

        # Enable broadcast
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def listen_for_offers(self):
        buffer = b''
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(2048)  # Increase buffer size to 2048 bytes
                buffer += data
                while len(buffer) >= 9:
                    offer_message = buffer[:9]
                    buffer = buffer[9:]
                    magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', offer_message)
                    if magic_cookie == 0xabcddcba and message_type == 0x2:
                        print(f"Received offer from {addr[0]}: UDP port {udp_port}, TCP port {tcp_port}")
                        return addr[0], udp_port, tcp_port
            except Exception as e:
                print(f"Error receiving offer: {e}")

    def send_udp_request(self, server_ip, udp_port, file_size, udp_index):
        try:
            # Create request message
            magic_cookie = 0xabcddcba
            message_type = 0x3
            request_message = struct.pack('!IBQ', magic_cookie, message_type, file_size)
            self.udp_socket.sendto(request_message, (server_ip, udp_port))
            # print(f"Sent UDP request to {server_ip}:{udp_port}")
            
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
                    # Ignore offer messages
                    if len(data) == 9 and data[:4] == struct.pack('!I', 0xabcddcba) and data[4] == 0x2:
                        continue
                    magic_cookie, message_type, total_segments, current_segment = struct.unpack('!IBQQ', data[:21])
                    if magic_cookie != 0xabcddcba or message_type != 0x4:
                        continue  # Invalid payload message
                    payload = data[21:]
                    bytes_received += len(payload)  # Use the length of the payload directly
                    last_packet_time = time.time()
                    # print(f"Received UDP data from {addr}: {data}")
                except socket.timeout:
                    if time.time() - last_packet_time > 1:
                        break

            end_time = time.time()
            total_time = end_time - start_time
            speed = (bytes_received * 8) / total_time
            # packet_loss = ((file_size - bytes_received) / file_size) * 100 if file_size > 0 else 0
            packets_received_percentage = (bytes_received / file_size) * 100 if file_size > 0 else 0

            print(f"UDP transfer #{udp_index} finished, total time: {total_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {packets_received_percentage:.2f}%")
        except Exception as e:
            print(f"Error: {e}")

    def send_tcp_request(self, server_ip, tcp_port, file_size, tcp_index):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((server_ip, tcp_port))
            # print(f"Connected to TCP server at {server_ip}:{tcp_port}")
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

    def start(self):
        file_size = int(input("Enter the file size for the speed test (in bytes): "))
        tcp_connections = int(input("Enter the number of TCP connections: "))
        udp_connections = int(input("Enter the number of UDP connections: "))
        while True:
            print("Client started, listening for offer requests...")
            server_ip, udp_port, tcp_port = self.listen_for_offers()

            threads = []

            for i in range(tcp_connections):
                tcp_thread = threading.Thread(target=self.send_tcp_request, args=(server_ip, tcp_port, file_size, i + 1))
                threads.append(tcp_thread)
                tcp_thread.start()

            for i in range(udp_connections):
                udp_thread = threading.Thread(target=self.send_udp_request, args=(server_ip, udp_port, file_size, i + 1))
                threads.append(udp_thread)
                udp_thread.start()

            for thread in threads:
                thread.join()
                
            print("\nAll transfers complete, listening to offer requests\n")

def main():
    parser = argparse.ArgumentParser(description="Network Speed Test Client")
    parser.add_argument('--listen_port', type=int, default=5003, help="Client listen port for offers")
    args = parser.parse_args()

    client = SpeedTestClient(listen_port=args.listen_port)
    client.start()

if __name__ == "__main__":
    main()