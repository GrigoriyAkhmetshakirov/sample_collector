import socket
import struct
import time
import random

UDP_IP = "127.0.0.1"
UDP_PORT = 49049
SEND_INTERVAL = 0.01 # Интервал отправки

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

num_pack = 0

def generate_packet():

    global num_pack

    values = [random.uniform(-100, -90) for _ in range(512)] + [random.uniform(-90, -50) for _ in range(512)] + [random.uniform(-50, -30) for _ in range(512)] + [random.uniform(-100, -50) for _ in range(512)]
    num_pack += 1
    num_ant = 1
    num_win = random.randint(1, 21)
    diag = 1

    packed_data = struct.pack('2048f I B B B', *values, num_pack, num_ant, num_win, diag)
    
    return packed_data

try:
    print(f'Отправка UDP-пакетов на {UDP_IP}:{UDP_PORT}...')

    while True:
        packet = generate_packet()
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        print(f'Отправлен пакет {num_pack}')
        time.sleep(SEND_INTERVAL)

except KeyboardInterrupt:
    print('\nПередача остановлена.')

finally:
    sock.close()
