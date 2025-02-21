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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
        "sleep_time": 0.5,  # Полсекунды задержка
        "window_size": [800, 600]
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
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.label_type = QLabel(f'Тип купола:', self)
        layout.addWidget(self.label_type)
        self.combo_system = QComboBox(self)
        self.combo_system.addItems(SYSTEM_TYPES)
        layout.addWidget(self.combo_system)

        self.drone_type = QLabel(f'Тип дрона:', self)
        layout.addWidget(self.drone_type)
        self.combo_drone = QComboBox(self)
        self.combo_drone.addItems(DRONE_TYPES)
        layout.addWidget(self.combo_drone)

        self.btn_start = QPushButton('Начать сбор данных', self)
        self.btn_start.clicked.connect(self.start_receiving)
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton('Остановить сбор данных', self)
        self.btn_stop.clicked.connect(self.stop_receiving)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        # Матplotlib canvas для графика
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.text_output = QTextEdit(self)
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)

        self.setLayout(layout)
        self.setWindowTitle('UDP Receiver')

        # Данные для графика
        self.data_x = []  # Индекс пакетов
        self.data_y = []  # Значения сигнала

        # Счетчик для индекса
        self.index = 0

    def start_receiving(self):
        '''Запуск приема UDP-пакетов'''
        self.is_receiving = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.text_output.clear()
        self.thread = threading.Thread(target=self.receive_data)
        self.thread.start()

    def stop_receiving(self):
        '''Остановка приема UDP-пакетов'''
        self.is_receiving = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        time.sleep(1)
        self.text_output.clear()

    def receive_data(self):
        '''Функция приема и записи данных'''
        while self.is_receiving:
            message, _ = self.socket.recvfrom(8200)
            data = np.frombuffer(message[:8192], dtype=np.float32)

            # Здесь пример использования данных для построения графика
            signal_strength = np.mean(data)  # Например, используем среднее значение как "сигнал"

            # Добавляем данные на график
            self.data_x.append(self.index)
            self.data_y.append(signal_strength)

            # Ограничиваем количество точек, чтобы график не разрастался
            if len(self.data_x) > 100:
                self.data_x.pop(0)
                self.data_y.pop(0)

            # Обновляем график (столбчатый график)
            self.ax.clear()
            self.ax.bar(self.data_x, self.data_y)
            self.ax.set_xlabel("Пакет")
            self.ax.set_ylabel("Сила сигнала")
            self.ax.set_title("Изменение силы сигнала в реальном времени")
            self.canvas.draw()

            # Обновляем текстовое сообщение
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            message = f'{timestamp} Signal Strength: {signal_strength:.2f}'
            self.text_output.append(message)

            # Увеличиваем индекс для оси X
            self.index += 1

            # Добавляем задержку в 0.5 секунды
            time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    receiver = UDPReceiver()
    receiver.show()
    sys.exit(app.exec_())
