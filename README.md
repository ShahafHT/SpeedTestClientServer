# Network Speed Test Client-Server Application

This project implements a multi-threaded client-server application for conducting network speed tests. The application consists of a client that connects to a server and measures the speed of the network connection using both TCP and UDP protocols.

## Project Structure

```
network-speed-test
├── src
│   ├── client.py        # Multi-threaded client application for speed testing
│   ├── server.py        # Multi-threaded server application responding to client requests
│   └── __init__.py      # Initialization file for the src package
├── requirements.txt      # Dependencies required for the project
└── README.md             # Documentation for the project
```

## Getting Started

### Prerequisites

Make sure you have Python installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd network-speed-test
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the server:
   ```
   python src/server.py
   ```

2. In a separate terminal, start the client:
   ```
   python src/client.py
   ```

### Usage

- The client will prompt you for parameters such as the server address and the type of speed test (TCP/UDP).
- The server will continuously listen for incoming connections and respond to speed test requests.

## Packet Formats

- The client and server communicate using specific packet formats defined in the application. Ensure to refer to the source code for detailed information on the packet structure.

## Architecture

- The application is designed to handle multiple clients simultaneously using threading. The server spawns a new thread for each client connection, allowing for concurrent speed tests.

## Contributing

Feel free to submit issues or pull requests if you have suggestions for improvements or new features.

## License

This project is licensed under the MIT License - see the LICENSE file for details.