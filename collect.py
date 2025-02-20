import sys
import os
import socket
import struct
import csv
import time
import threading
import numpy as np
import datetime
import json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QTextEdit

# Загружаем конфиг из JSON
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
        "sleep_time": 5,
        "window_size": [400, 600]
    }

UDP_IP = config["udp_ip"]
UDP_PORT = config["udp_port"]
SEND_TO_IP = config["send_to_ip"]
SEND_TO_PORT = config["send_to_port"]
DRONE_TYPES = config["drone_types"]
SYSTEM_TYPES = config["system_types"]
SLEEP_TIME = config["sleep_time"]
WINDOW_WIDTH, WINDOW_HEIGHT = config["window_size"]

if not os.path.exists('data'):
    os.mkdir('data')
os.chdir('data')

class UDPReceiver(QWidget):
    def __init__(self):
        super().__init__()

        self.is_receiving = False
        self.thread = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((UDP_IP, UDP_PORT))
        self.socket.sendto(bytes("STR\n", "ascii"), (SEND_TO_IP, SEND_TO_PORT))

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Размер окна из config.json

        self.label_type = QLabel(f'Тип купола:', self)
        layout.addWidget(self.label_type)
        self.combo_system = QComboBox(self)
        self.combo_system.addItems(SYSTEM_TYPES)  # Загружаем из config.json
        layout.addWidget(self.combo_system)

        self.drone_type = QLabel(f'Тип дрона:', self)
        layout.addWidget(self.drone_type)
        self.combo_drone = QComboBox(self)
        self.combo_drone.addItems(DRONE_TYPES)  # Загружаем из config.json
        layout.addWidget(self.combo_drone)

        self.btn_start = QPushButton('Начать сбор данных', self)
        self.btn_start.clicked.connect(self.start_receiving)
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton('Остановить сбор данных', self)
        self.btn_stop.clicked.connect(self.stop_receiving)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        self.text_output = QTextEdit(self)
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)

        self.setLayout(layout)
        self.setWindowTitle('UDP Receiver')

    def start_receiving(self):
        '''Запуск приема UDP-пакетов'''
        self.is_receiving = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.text_output.clear()
        self.thread = threading.Thread(target=self.receive_data)
        self.thread.start()
        self.text_output.append(f'Запись в файл {self.file_name} начата')

    def stop_receiving(self):
        '''Остановка приема UDP-пакетов'''
        self.is_receiving = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        time.sleep(1)
        self.text_output.clear()
        self.text_output.append(f'Запись в файл {self.file_name} окончена')

    def receive_data(self):
        '''Функция приема и записи данных'''
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_name = f'data_{current_date}.csv'

        with open(self.file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['data' + str([x]) for x in range(2048)] + ['Num Pack', 'Antenna', 'Window', 'Diag', 'System_type', 'Drone_type'])
            while self.is_receiving:
                message, _ = self.socket.recvfrom(8200)
                data = np.frombuffer(message[:8192], dtype=np.float32)
                data = [data[x] for x in range(len(data))]
                num_pack = int(np.frombuffer(message[8192:8196], dtype=np.uint32))
                num_ant = int(np.frombuffer(message[8196:8197], dtype=np.uint8))
                num_win = int(np.frombuffer(message[8197:8198], dtype=np.uint8))
                diag = int(np.frombuffer(message[8198:8199], dtype=np.uint8))

                writer.writerow([*data, num_pack, num_ant, num_win, diag, self.combo_system.currentText(), self.combo_drone.currentText()])

                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                message = f'{timestamp} received {num_pack} package'
                self.text_output.append(message)
                time.sleep(SLEEP_TIME)  # Используем значение из config.json
                print(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    receiver = UDPReceiver()
    receiver.show()
    sys.exit(app.exec_())
