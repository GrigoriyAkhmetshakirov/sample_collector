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
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QTextEdit,  QMessageBox
from subprocess import Popen


# Загружаем конфиг из JSON
CONFIG_FILE = "config1.json"

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
        "window_size": [400, 600],
        # "PATH":'C:\\Python_Projects\\sample_collector\\gr2.py'
    }

UDP_IP = config["udp_ip"]
UDP_PORT = config["udp_port"]
SEND_TO_IP = config["send_to_ip"]
SEND_TO_PORT = config["send_to_port"]
DRONE_TYPES = config["drone_types"]
SYSTEM_TYPES = config["system_types"]
SLEEP_TIME = config["sleep_time"]
WINDOW_WIDTH, WINDOW_HEIGHT = config["window_size"]
PATH = os.path.join(os.getcwd(), 'gr2.py')

if not os.path.exists('data'):
    os.mkdir('data')
os.chdir('data')

print(os.getcwd())

class UDPReceiver(QWidget):
    def __init__(self):
        super().__init__()

        self.is_receiving = False
        self.thread = None
        self.file_name ="Not yet"

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((UDP_IP, UDP_PORT))
        self.socket.sendto(bytes("STR\n", "ascii"), (SEND_TO_IP, SEND_TO_PORT))

        self.start_name_server()  # Запуск сервера для получения NAME_FILE

        self.initUI()

    def start_name_server(self):
        self.name_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name_server_socket.bind(('127.0.0.1', 12345))  # localhost
        self.name_server_socket.listen(5)

        print("Сервер для NAME запущен на 127.0.0.1:12345")

        self.name_server_thread = threading.Thread(target=self.send_name_to_client)
        self.name_server_thread.daemon = True  # Чтобы поток завершился при выходе из программы
        self.name_server_thread.start()

    def send_name_to_client(self):
        while True:
            client_socket, address = self.name_server_socket.accept()
            print(f"Подключение от {address}")

            # Получение запроса от клиента
            request = client_socket.recv(1024).decode('utf-8')
            print(f"Запрос: {request}")

            if request == "get_name":
                name = self.file_name
                client_socket.send(name.encode('utf-8'))
            else:
                client_socket.send("Unknown request".encode('utf-8'))

            client_socket.close()

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

        self.btn_plot = QPushButton('Запустить визуализацию', self)
        self.btn_plot.clicked.connect(self.run_signal_plotter)
        layout.addWidget(self.btn_plot)

        # Добавляем кнопку очистки
        self.btn_clear = QPushButton('Очистить каталог', self)
        self.btn_clear.clicked.connect(self.clear_directory)
        layout.addWidget(self.btn_clear)

    def run_signal_plotter(self):
        Popen(['python', PATH])

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

    def clear_directory(self):

        files = os.listdir()

        if not files:
            QMessageBox.information(self, "Информация", "Каталог пуст")
            return

        message = f"Вы уверены, что хотите удалить все файлы из каталога?\n\n" \
                  f"Текущий каталог: {os.getcwd()}\n\n" \
                  f"Файлы для удаления:\n" + "\n".join(files)

        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
               ## Удаляем все файлы
                for file in files:
                    if os.path.isfile(file):
                        os.remove(file)
                QMessageBox.information(
                    self,
                    "Успешно",
                    "Все файлы успешно удалены"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Произошла ошибка при удалении файлов: {str(e)}"
                )

    def receive_data(self):
        '''Функция приема и записи данных'''
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.file_name = f'data_{current_date}.csv'

        expected_win = None  # Переменная для отслеживания ожидаемого значения num_win

        with open(self.file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['data' + str([x]) for x in range(2048)] + ['Num Pack', 'Antenna', 'Window', 'Diag', 'System_type', 'Drone_type'])
            while self.is_receiving:

                message, _ = self.socket.recvfrom(8200)
                data = np.frombuffer(message[:8192], dtype=np.float32)
                data = [data[x] for x in range(len(data))]
                num_pack = np.frombuffer(message[8192:8196], dtype=np.uint32)[0]
                num_ant = np.frombuffer(message[8196:8197], dtype=np.uint8)[0]
                num_win = np.frombuffer(message[8197:8198], dtype=np.uint8)[0]
                diag = np.frombuffer(message[8198:8199], dtype=np.uint8)[0]
                writer.writerow([*data, num_pack, num_ant, num_win, diag, self.combo_system.currentText(), self.combo_drone.currentText()])

                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                message = f'{timestamp} received {num_pack} package num_ant= {num_ant} num_win= {num_win}'
                self.text_output.append(message)
                time.sleep(SLEEP_TIME)  # Используем значение из config.json
                print(message)

                # Если это первый пакет с num_win=1, начинаем контроль
                if num_win == 1 and expected_win is None:
                    expected_win = 2  # Ожидаем следующий пакет с num_win=2
                else:
                    # Если контроль начат, проверяем последовательность пакетов
                    if expected_win is not None and expected_win != num_win:
                        print(f'Предупреждение: ожидаемый num_win={expected_win}, получен num_win={num_win}')
                    # Обновляем ожидаемое значение num_win
                    if expected_win is not None:
                        if num_win == 12:
                            expected_win = 1  # После 12 ожидаем 1
                        else:
                            expected_win += 1

if __name__ == '__main__':
    app = QApplication(sys.argv)
    receiver = UDPReceiver()
    receiver.show()
    sys.exit(app.exec_())
