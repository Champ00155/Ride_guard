import socket

ESP32_IP = "192.168.4.1"
ESP32_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

message = "LEFT"

sock.sendto(message.encode(), (ESP32_IP, ESP32_PORT))

print(f"Sent: {message}")

sock.close()
