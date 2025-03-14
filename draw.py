import matplotlib.pyplot as plt
import socket
import os
import json
import numpy as np

CONFIG_FILE = "config.json"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    print(f"Файл {CONFIG_FILE} не найден! Используются стандартные значения.")
    config = {
        "udp_ip": "192.168.2.126",
        "udp_port": 49049,
        "send_to_ip": "192.168.2.10",
        "send_to_port": 5023,
        "drone_types": ["DJI", "Autel"],
        "system_types": ["Type 1", "Type 2", "Type 3"],
        "sleep_time": 1,
        "window_size": [20, 5],
        "selected_antenna": 1,
        "selected_window": 1,
        "antenna_list": [1],
        "window_list": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
    }

UDP_IP = config["udp_ip"]
UDP_PORT = config["udp_port"]
SEND_TO_IP = config["send_to_ip"]
SEND_TO_PORT = config["send_to_port"]
DRONE_TYPES = config["drone_types"]
SYSTEM_TYPES = config["system_types"]
SLEEP_TIME = config["sleep_time"]
WINDOW_WIDTH, WINDOW_HEIGHT = config["window_size"]
ANTENNA_LIST = config["antenna_list"]
WINDOW_LIST = config["window_list"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.sendto(b"STR\n", (SEND_TO_IP, SEND_TO_PORT))

def get_and_parse_message():
    try:
        message, _ = sock.recvfrom(8200)
        data = np.frombuffer(message[:8192], dtype=np.float32)
        num_pack = np.frombuffer(message[8192:8196], dtype=np.uint32)[0]
        num_ant = np.frombuffer(message[8196:8197], dtype=np.uint8)[0]
        num_win = np.frombuffer(message[8197:8198], dtype=np.uint8)[0]
        return data, num_pack, num_ant, num_win
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None

plt.ion()

num_rows = 3  # Количество строк
num_cols = 7  # Количество столбцов

fig, axes = plt.subplots(num_rows, num_cols, figsize=(WINDOW_WIDTH, WINDOW_HEIGHT))
fig.canvas.manager.set_window_title('Data Visualizer')
plt.tight_layout()

# Подготовка линий для каждого subplot
lines = {}
for ant_idx, ant in enumerate(ANTENNA_LIST):
    for win_idx, win in enumerate(WINDOW_LIST):
        ax = axes[win_idx // num_cols, win_idx % num_cols]
        ax.set_title(f'Window {win}')
        # ax.set_xlabel('Index')
        # ax.set_ylabel('Value')
        ax.set_xlim(0, 2047) 
        ax.set_ylim(-100, 10)
        line, = ax.plot([], [])
        lines[(ant, win)] = line

while True:
    result = get_and_parse_message()
    if result is None:
        continue
    data, num_pack, num_ant, num_win = result
    
    if num_ant in ANTENNA_LIST and num_win in WINDOW_LIST:
        key = (num_ant, num_win)
        lines[key].set_data(np.arange(2048), data)
        ax = lines[key].axes
        ax.relim()
        ax.autoscale_view(True, True, False)
    
    plt.draw()
    plt.pause(SLEEP_TIME)

sock.close()
plt.ioff()