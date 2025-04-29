import sys
import json
import os
import socket
import csv
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QVBoxLayout, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import datetime
import time

CONFIG_FILE = 'config.json'
DOME_CONFIG_FILE = 'dome_config.json'

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    print('Config file is not exist!')

if os.path.exists(DOME_CONFIG_FILE):
    with open(DOME_CONFIG_FILE, 'r') as f:
        dome_config = json.load(f)
else:
    print('Dome config file is not exist!')

if not os.path.exists('data'):
    os.mkdir('data')

FREQ_CONFIGS = {
    f'{config.get("system_types")[0]}': {
        1: {'central': 420, 'range': 20},
        2: {'central': 460, 'range': 20},
        3: {'central': 715, 'range': 20},
        4: {'central': 880, 'range': 20},
        5: {'central': 920, 'range': 20},
        6: {'central': 1220, 'range': 20},
        7: {'central': 1260, 'range': 20},
        8: {'central': 2420, 'range': 20},
        9: {'central': 2460, 'range': 20},
        10: {'central': 5160, 'range': 20},
        11: {'central': 5200, 'range': 20},
        12: {'central': 5240, 'range': 20},
        13: {'central': 5640, 'range': 20},
        14: {'central': 5680, 'range': 20},
        15: {'central': 5720, 'range': 20},
        16: {'central': 5760, 'range': 20},
        17: {'central': 5800, 'range': 20},
        18: {'central': 5840, 'range': 20},
        19: {'central': 5880, 'range': 20},
        20: {'central': 5920, 'range': 20},
        21: {'central': 5960, 'range': 20},
    },
    f'{config.get("system_types")[1]}': {
        1: {'central': 420, 'range': 20},
        2: {'central': 460, 'range': 20},
        3: {'central': 880, 'range': 20},
        4: {'central': 920, 'range': 20},
        5: {'central': 2420, 'range': 20},
        6: {'central': 2460, 'range': 20},
        7: {'central': 5160, 'range': 20},
        8: {'central': 5200, 'range': 20},
        9: {'central': 5240, 'range': 20},
        10: {'central': 5760, 'range': 20},
        11: {'central': 5800, 'range': 20},
        12: {'central': 5840, 'range': 20},
    },
    f'{config.get("system_types")[2]}': {
        1: {'central': 420, 'range': 20},
        2: {'central': 460, 'range': 20},
        3: {'central': 880, 'range': 20},
        4: {'central': 920, 'range': 20},
        5: {'central': 2420, 'range': 20},
        6: {'central': 2460, 'range': 20},
        7: {'central': 5160, 'range': 20},
        8: {'central': 5200, 'range': 20},
        9: {'central': 5240, 'range': 20},
        10: {'central': 5640, 'range': 20},
        11: {'central': 5680, 'range': 20},
        12: {'central': 5720, 'range': 20},
        13: {'central': 5760, 'range': 20},
        14: {'central': 5800, 'range': 20},
        15: {'central': 5840, 'range': 20},
        16: {'central': 5880, 'range': 20},
        17: {'central': 5920, 'range': 20},
        18: {'central': 5960, 'range': 20},
    },
}

class UdpWorker(QtCore.QObject):
    data_received = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self, config):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((config['udp_ip'], config['udp_port']))
        self.sock.sendto(b'STR\n', (config['send_to_ip'], config['send_to_port']))
        self.running = True

    def run(self):
        print('Start receiving')
        while self.running:
            try:
                message, _ = self.sock.recvfrom(8200)
                data = np.frombuffer(message[:8192], dtype=np.float32)
                num_pack = np.frombuffer(message[8192:8196], dtype=np.uint32)[0]
                num_ant = np.frombuffer(message[8196:8197], dtype=np.uint8)[0]
                num_win = np.frombuffer(message[8197:8198], dtype=np.uint8)[0]
                self.data_received.emit(data, num_pack, num_ant, num_win)
            except Exception as e:
                print(f'Ошибка при получении данных: {e}')

    def stop(self):
        print('Stop receiving')
        self.running = False
        self.sock.sendto(b'FIN\n', (config['send_to_ip'], config['send_to_port']))
        
    def close(self):
        self.stop()
        self.sock.close()

    def send_command(self, command):
        # self.stop()
        command = bytes('CFG ' + command + '\n', 'ascii')
        print(command)
        self.sock.sendto(command, (config['send_to_ip'], config['send_to_port']))
        time.sleep(1)
        self.sock.sendto(b'CFG?\n', (config['send_to_ip'], config['send_to_port']))
        # print(self.sock.recvfrom(8200))
        # self.sock.sendto(b'CFGMEMWRITE\n', (config['send_to_ip'], config['send_to_port']))
        time.sleep(1)
        self.sock.sendto(b'STR\n', (config['send_to_ip'], config['send_to_port']))
        # self.running = True
        # self.run()
        print('End sending command')
        
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.xdata_map = {}
        self.lines = {}
        self.canvases = {}
        self.canvas_size = config.get('canvas_size')
        self.initUI()
        self.initUdp()
        self.is_writing = False
        self.file = None
        self.iter = config.get('iters') # Счетчик частоты записи данных в файл

    def initUI(self):
        self.setGeometry(150, 150, 1600, 800)
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Элементы управления передачей и записи параметров
        control_panel = QtWidgets.QGroupBox('Параметры записи')
        control_layout = QtWidgets.QVBoxLayout()
        control_panel.setLayout(control_layout)

        # control_panel.setFixedWidth(200)
        # control_panel.setFixedHeight(400)
        # control_panel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        
        self.label_type = QLabel(f'Тип купола:', self)
        control_layout.addWidget(self.label_type, alignment=QtCore.Qt.AlignTop)
        self.combo_system = QComboBox(self)
        self.combo_system.addItems(config.get('system_types', []))
        self.combo_system.currentTextChanged.connect(self.update_frequency_config)
        control_layout.addWidget(self.combo_system, alignment=QtCore.Qt.AlignTop)
        self.FREQUENCY_CONFIG = FREQ_CONFIGS[self.combo_system.currentText()]

        self.drone_type = QLabel(f'Тип дрона:', self)
        control_layout.addWidget(self.drone_type, alignment=QtCore.Qt.AlignTop)
        self.combo_drone = QComboBox(self)
        self.combo_drone.addItems(config.get('drone_types', []))
        control_layout.addWidget(self.combo_drone, alignment=QtCore.Qt.AlignTop)

        self.btn_start = QPushButton('Начать сбор данных', self)
        self.btn_start.clicked.connect(self.start_writing_to_file)
        control_layout.addWidget(self.btn_start, alignment=QtCore.Qt.AlignTop)

        self.btn_stop = QPushButton('Остановить сбор данных', self)
        self.btn_stop.clicked.connect(self.stop_writing_to_file)
        self.btn_stop.setEnabled(False)
        control_layout.addWidget(self.btn_stop, alignment=QtCore.Qt.AlignTop)

        # Чекбокс присутствия дрона
        self.drone_present_cb = QtWidgets.QCheckBox('Дрон присутствует', self)
        control_layout.addWidget(self.drone_present_cb, alignment=QtCore.Qt.AlignTop)

        self.window_type = QLabel(f'Оконная функция:', self)
        control_layout.addWidget(self.window_type, alignment=QtCore.Qt.AlignTop)
        self.combo_window_type = QComboBox(self)
        self.combo_window_type.addItems(config.get('window_type', []))
        control_layout.addWidget(self.combo_window_type, alignment=QtCore.Qt.AlignTop)

        self.avg = QLabel(f'Количество усреднений:', self)
        control_layout.addWidget(self.avg, alignment=QtCore.Qt.AlignTop)
        self.combo_avg = QComboBox(self)
        self.combo_avg.addItems(config.get('avg', []))
        control_layout.addWidget(self.combo_avg, alignment=QtCore.Qt.AlignTop)

        self.btn_send_configs = QPushButton('Обновить параметры купола', self)
        self.btn_send_configs.clicked.connect(self.send_configs_to_dome)
        control_layout.addWidget(self.btn_send_configs, alignment=QtCore.Qt.AlignTop)

        # Добавляем кнопку очистки
        self.btn_clear = QPushButton('Очистить каталог', self)
        self.btn_clear.clicked.connect(self.clear_directory)
        control_layout.addWidget(self.btn_clear)

        main_layout.addWidget(control_panel, alignment=QtCore.Qt.AlignTop)

        # Элементы управления окнами
        checkbox_panel = QtWidgets.QGroupBox('Параметры окон')
        self.checkboxes_layout = QtWidgets.QVBoxLayout()
        checkbox_panel.setLayout(self.checkboxes_layout)

        enable_all_btn = QtWidgets.QPushButton('Включить все окна')
        enable_all_btn.clicked.connect(self.enable_all_windows)
        self.checkboxes_layout.addWidget(enable_all_btn)

        disable_all_btn = QtWidgets.QPushButton('Выключить все окна')
        disable_all_btn.clicked.connect(self.disable_all_windows)
        self.checkboxes_layout.addWidget(disable_all_btn)

        # Инициализируем чекбоксы
        self.checkboxes = {}
        self.update_checkboxes()
        self.checkboxes_layout.addStretch()
        main_layout.addWidget(checkbox_panel, alignment=QtCore.Qt.AlignTop)
        
        # Панель с графиками
        right_layout = QtWidgets.QVBoxLayout()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        plot_container = QtWidgets.QWidget()
        self.plot_layout = QtWidgets.QGridLayout(plot_container)
        scroll.setWidget(plot_container)
        right_layout.addWidget(scroll)

        self.rebuild_plots()
        self.plot_layout.setRowStretch(self.plot_layout.rowCount(), 1)
        self.plot_layout.setColumnStretch(self.plot_layout.columnCount(), 1)
        # self.update_plot_layout()
        
        close_button = QtWidgets.QPushButton('Закрыть')
        close_button.clicked.connect(self.close)
        right_layout.addWidget(close_button, alignment=QtCore.Qt.AlignRight)
        main_layout.addLayout(right_layout)

    def update_frequency_config(self):
        self.dome_type = self.combo_system.currentText()
        self.FREQUENCY_CONFIG = FREQ_CONFIGS[self.dome_type]
        self.update_checkboxes() 
        self.rebuild_plots()
        self.update_plot_titles()

    def update_checkboxes(self):
        for win_num in list(self.checkboxes.keys()):
            self.checkboxes[win_num].setParent(None)
            del self.checkboxes[win_num]
        for win_num in self.FREQUENCY_CONFIG:
            cfg = self.FREQUENCY_CONFIG[win_num]
            cb = QtWidgets.QCheckBox(f'{cfg['central']} МГц')
            cb.setChecked(win_num in config['window_list'])
            cb.stateChanged.connect(lambda state, wn=win_num: self.toggle_window(wn, state))
            self.checkboxes_layout.addWidget(cb)
            self.checkboxes[win_num] = cb

    def update_plot_titles(self):
        for win_num in self.FREQUENCY_CONFIG:
            if win_num in self.lines:
                ax = self.lines[win_num].axes
                cfg = self.FREQUENCY_CONFIG[win_num]
                start = cfg['central'] - cfg['range']
                end = cfg['central'] + cfg['range']
                ax.set_xticks([start, cfg['central'], end])
                ax.set_xlim(start, end)
                ax.figure.canvas.draw() 

    def rebuild_plots(self):
        for win_num in list(self.lines.keys()):
            self.plot_layout.removeWidget(self.canvases[win_num])
            self.canvases[win_num].deleteLater()
            del self.lines[win_num]
            del self.canvases[win_num]
            del self.xdata_map[win_num]

        for win_num in self.FREQUENCY_CONFIG:
            fig = Figure()
            canvas = FigureCanvas(fig)
            canvas.setFixedSize(*self.canvas_size)
            ax = fig.add_subplot(111)
            cfg = self.FREQUENCY_CONFIG[win_num]
            start = cfg['central'] - cfg['range']
            end = cfg['central'] + cfg['range']
            self.xdata_map[win_num] = np.linspace(start, end, 2048)
            ax.set_xticks([start, cfg['central'], end])
            ax.grid(True)
            ax.set_xlim(start, end)
            ax.set_ylim(-100, 10)
            line, = ax.plot([], [])
            self.lines[win_num] = line
            self.canvases[win_num] = canvas
            row = (win_num - 1) // config.get('grid')
            col = (win_num - 1) % config.get('grid')
            self.plot_layout.addWidget(canvas, row, col)
            canvas.setVisible(win_num in config['window_list'])

        self.update_plot_layout()

    def update_plot_layout(self):
        for i in reversed(range(self.plot_layout.count())):
            widget = self.plot_layout.itemAt(i).widget()
            if widget:
                self.plot_layout.removeWidget(widget)
        active_windows = sorted(
            [win for win in config['window_list'] if win in self.canvases],
            key=lambda win: self.FREQUENCY_CONFIG[win]['central']
        )
        for index, win_num in enumerate(active_windows):
            row = index // config.get('grid')
            col = index % config.get('grid')
            self.plot_layout.addWidget(self.canvases[win_num], row, col)
            self.canvases[win_num].setVisible(True)
    
    def enable_all_windows(self):
        for win_num, cb in self.checkboxes.items():
            cb.setChecked(True)
        # config['window_list'].clear()
        for canvas in self.canvases.values():
            canvas.setVisible(True)

    def disable_all_windows(self):
        for win_num, cb in self.checkboxes.items():
            cb.setChecked(False)
        config['window_list'].clear()
        for canvas in self.canvases.values():
            canvas.setVisible(False)

    def toggle_window(self, win_num, state):
        if state == QtCore.Qt.Checked:
            if win_num not in config['window_list']:
                config['window_list'].append(win_num)
        else:
            if win_num in config['window_list']:
                config['window_list'].remove(win_num)
        self.canvases[win_num].setVisible(state == QtCore.Qt.Checked)
        self.update_plot_layout()

    def initUdp(self):
        self.udp_thread = QtCore.QThread()
        self.udp_worker = UdpWorker(config)
        self.udp_worker.moveToThread(self.udp_thread)
        self.udp_thread.started.connect(self.udp_worker.run)
        self.udp_worker.data_received.connect(self.get_data_update_plot)
        self.udp_thread.start()

    def start_writing_to_file(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.is_writing = True
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.file = open(f'data/data_{current_date}.csv', 'w')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['data' + str([x]) for x in range(2048)] + ['Mean', 'Num Pack', 'Antenna', 'Window', 'System_type', 'Drone_type', 'Drone_is_present', 'Timestamp'])

    def stop_writing_to_file(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        # self.udp_worker.stop()
        self.is_writing = False
        time.sleep(1)
        self.file.close()

    def get_data_update_plot(self, data, num_pack, num_ant, num_win):
        if self.is_writing and len(data) == 2048 and (self.iter % config.get('iters')) == 0:
            self.writer.writerow([*data, np.mean(data), num_pack, num_ant, num_win, self.combo_system.currentText(), self.combo_drone.currentText(), int(self.drone_present_cb.isChecked()), datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')])
            self.iter = 0
        self.iter += 1
        if num_ant in config['antenna_list'] and num_win in config['window_list']:
            if num_win in self.lines:
                xdata = self.xdata_map[num_win]
                self.lines[num_win].set_data(xdata, data)
                ax = self.lines[num_win].axes
                ax.relim()
                ax.autoscale_view(True, True, False)
                self.canvases[num_win].draw_idle()

    def send_configs_to_dome(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if self.dome_type == f'{config.get("system_types")[0]}':
            command = '2097151'
        elif self.dome_type == f'{config.get("system_types")[1]}':
            command = '4095'
        else:
            command = '262143'
        command += ' 255' + ' ' \
            + dome_config['lna'] + ' ' \
            + dome_config['gain1'] + ' ' \
            + dome_config['gain2'] + ' ' \
            + dome_config['gain3'] + ' ' \
            + dome_config['gain4'] + ' ' \
            + dome_config['gain5'] + ' ' \
            + self.combo_window_type.currentText() + ' ' \
            + self.combo_avg.currentText()
        self.udp_worker.send_command(command)

    def clear_directory(self):
        files = os.listdir('data')
        if not files:
            QMessageBox.information(self, "Информация", "Каталог пуст")
            return
 
        message = f"Вы уверены, что хотите удалить все файлы из каталога?\n\n" \
                f"Файлы для удаления:\n" + "\n".join(files)
 
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                for file in files:
                    os.remove(os.path.join(os.getcwd(), 'data', file))
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

    def closeEvent(self, event):
        self.file.close() if self.file is not None else None
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        with open(DOME_CONFIG_FILE, 'w') as f:
            json.dump(dome_config, f, indent=4)
        self.udp_worker.close()
        self.udp_thread.quit()
        self.udp_thread.wait()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(config)
    main.show()
    sys.exit(app.exec_())
