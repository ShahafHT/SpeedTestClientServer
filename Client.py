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

    def send_udp_request(self, file_size, udp_index):
        try:
            # Create request message
            magic_cookie = 0xabcddcba
            message_type = 0x3
            request_message = struct.pack('!IBQ', magic_cookie, message_type, file_size)
            self.udp_socket.sendto(request_message, (self.server_ip, self.server_port + 1))
            print(f"Sent UDP request to {self.server_ip}:{self.server_port + 1}")
            
            start_time = time.time()
            received_packets = 0
            total_packets = 0

            # Receive payload
            while True:
                self.udp_socket.settimeout(1)
                try:
                    data, addr = self.udp_socket.recvfrom(1024)
                    if not data:
                        break
                    received_packets += 1
                    print(f"Received UDP data from {addr}: {data}")
                except socket.timeout:
                    break
                total_packets += 1

            end_time = time.time()
            total_time = end_time - start_time
            speed = (file_size * 8) / total_time
            packet_loss = ((total_packets - received_packets) / total_packets) * 100 if total_packets > 0 else 0

            print(f"UDP transfer #{udp_index} finished, total time: {total_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {100 - packet_loss:.2f}%")
        except Exception as e:
            print(f"Error: {e}")

    def send_tcp_request(self, file_size, tcp_index):
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            print(f"Connected to TCP server at {self.server_ip}:{self.server_port}")
            self.tcp_socket.sendall(f"{file_size}\n".encode())
            
            start_time = time.time()

            # Receive file
            while True:
                data = self.tcp_socket.recv(1024)
                if not data:
                    break
                print(f"Received TCP data: {data}")

            end_time = time.time()
            total_time = end_time - start_time
            speed = (file_size * 8) / total_time

            print(f"TCP transfer #{tcp_index} finished, total time: {total_time:.2f} seconds, total speed: {speed:.2f} bits/second")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.tcp_socket.close()

    def start(self):
        file_size = int(input("Enter the file size for the speed test: "))
        tcp_connections = int(input("Enter the number of TCP connections: "))
        udp_connections = int(input("Enter the number of UDP connections: "))

        threads = []

        for i in range(tcp_connections):
            tcp_thread = threading.Thread(target=self.send_tcp_request, args=(file_size, i + 1))
            threads.append(tcp_thread)
            tcp_thread.start()

        for i in range(udp_connections):
            udp_thread = threading.Thread(target=self.send_udp_request, args=(file_size, i + 1))
            threads.append(udp_thread)
            udp_thread.start()

        for thread in threads:
            thread.join()

        print("All transfers complete, listening to offer requests")