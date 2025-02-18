import sys
import os
import socket
import struct
import csv
import time
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QTextEdit

UDP_IP = '0.0.0.0'
UDP_PORT = 49049

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

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setFixedSize(400, 600)

        self.label_type = QLabel(f'Тип купола:', self)
        layout.addWidget(self.label_type)
        self.combo_system = QComboBox(self)
        self.combo_system.addItems(['Type 1', 'Type 2', 'Type 3'])
        layout.addWidget(self.combo_system)

        self.drone_type = QLabel(f'Тип дрона:', self)
        layout.addWidget(self.drone_type)
        self.combo_drone = QComboBox(self)
        self.combo_drone.addItems(['DJI', 'Autel'])
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
        self.setWindowTitle('')

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

        self.file_name = f'{time.strftime('%Y-%m-%d_%H:%M')}_data.csv'

        with open(self.file_name , 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['data' + str([x]) for x in range(2048)] + ['Num Pack', 'Antenna', 'Window', 'Diag', 'System_type', 'Drone_type']) 
            print()
            while self.is_receiving:
                message, _ = self.socket.recvfrom(8200)
                data=np.frombuffer(message[:8192], dtype=np.float32)
                data = [data[x] for x in range(len(data))]
                num_pack=int(np.frombuffer(message[8192:8196], dtype=np.uint32))
                num_ant=int(np.frombuffer(message[8196:8197], dtype=np.uint8))
                num_win=int(np.frombuffer(message[8197:8198], dtype=np.uint8))
                diag=int(np.frombuffer(message[8198:8199], dtype=np.uint8))

                writer.writerow([*data, num_pack, num_ant, num_win, diag, self.combo_system.currentText(), self.combo_drone.currentText()])
                
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                message = f'{timestamp} recieved {num_pack} package'
                self.text_output.append(message) 
                print(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    receiver = UDPReceiver()
    receiver.show()
    sys.exit(app.exec_())
