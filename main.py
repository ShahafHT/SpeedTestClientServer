import argparse
from Client import SpeedTestClient
from Server import SpeedTestServer

print("main.py is being executed")

def main():
    print("Entering main function")
    parser = argparse.ArgumentParser(description="Network Speed Test")
    parser.add_argument('role', choices=['client', 'server'], help="Role to play (client or server)")
    parser.add_argument('--host', default='0.0.0.0', help="Server IP address")
    parser.add_argument('--port', type=int, default=5001, help="Server port")
    parser.add_argument('--listen_port', type=int, default=5003, help="Client listen port for offers")  # Default to self.port + 2
    args = parser.parse_args()

    print(f"Role: {args.role}, Host: {args.host}, Port: {args.port}")

    if args.role == 'server':
        print("Starting server...")
        server = SpeedTestServer(ip=args.host, port=args.port)
        server.start()
    elif args.role == 'client':
        print("Starting client...")
        client = SpeedTestClient(listen_port=args.listen_port)
        client.start()

if __name__ == "__main__":
    print("Executing main block")
    main()