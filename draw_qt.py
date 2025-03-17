import sys
import json
import os
import socket
import csv
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import datetime

CONFIG_FILE = 'config.json'

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    print('Config file is not exist!')

if not os.path.exists('data'):
    os.mkdir('data')

FREQ_CONFIGS = {
    'Type 1': {
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
        21: {'central': 6950, 'range': 20},
    },
    'Type 2': {
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
    'Type 3': {
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
        self.running = False
        self.sock.close()

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

        
    def initUI(self):
        self.setGeometry(150, 150, 1600, 800)
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Элементы управления
        control_panel = QtWidgets.QGroupBox('Параметры')
        control_layout = QtWidgets.QVBoxLayout()
        control_panel.setLayout(control_layout)

        control_panel.setFixedWidth(200)
        control_panel.setFixedHeight(200)
        control_panel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        
        self.label_type = QLabel(f'Тип купола:', self)
        control_layout.addWidget(self.label_type)
        self.combo_system = QComboBox(self)
        self.combo_system.addItems(config.get('system_types', []))
        self.combo_system.currentTextChanged.connect(self.update_frequency_config)
        control_layout.addWidget(self.combo_system)
        self.FREQUENCY_CONFIG = FREQ_CONFIGS[self.combo_system.currentText()]

        self.drone_type = QLabel(f'Тип дрона:', self)
        control_layout.addWidget(self.drone_type)
        self.combo_drone = QComboBox(self)
        self.combo_drone.addItems(config.get('drone_types', []))
        control_layout.addWidget(self.combo_drone)

        self.btn_start = QPushButton('Начать сбор данных', self)
        self.btn_start.clicked.connect(self.start_receiving)
        control_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton('Остановить сбор данных', self)
        self.btn_stop.clicked.connect(self.stop_receiving)
        self.btn_stop.setEnabled(False)
        control_layout.addWidget(self.btn_stop)

        # Чекбокс присутствия дрона
        self.drone_present_cb = QtWidgets.QCheckBox('Дрон присутствует', self)
        control_layout.addWidget(self.drone_present_cb)
        
        main_layout.addWidget(control_panel, alignment=QtCore.Qt.AlignTop)
        
        checkbox_panel = QtWidgets.QGroupBox('Окна')
        self.checkboxes_layout = QtWidgets.QVBoxLayout()
        checkbox_panel.setLayout(self.checkboxes_layout)

        disable_all_btn = QtWidgets.QPushButton('Выключить все окна')
        disable_all_btn.clicked.connect(self.disable_all_windows)
        self.checkboxes_layout.addWidget(disable_all_btn)

        # Инициализируем чекбоксы
        self.checkboxes = {}
        self.update_checkboxes()
        self.checkboxes_layout.addStretch()
        main_layout.addWidget(checkbox_panel, alignment=QtCore.Qt.AlignTop)
        
        # Панель с графиками и кнопкой закрытия
        right_layout = QtWidgets.QVBoxLayout()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        plot_container = QtWidgets.QWidget()
        self.plot_layout = QtWidgets.QGridLayout(plot_container)
        scroll.setWidget(plot_container)
        right_layout.addWidget(scroll)
        
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

        self.plot_layout.setRowStretch(self.plot_layout.rowCount(), 1)
        self.plot_layout.setColumnStretch(self.plot_layout.columnCount(), 1)
        self.update_plot_layout()
        
        close_button = QtWidgets.QPushButton('Закрыть')
        close_button.clicked.connect(self.close)
        right_layout.addWidget(close_button, alignment=QtCore.Qt.AlignRight)
        main_layout.addLayout(right_layout)

    def update_frequency_config(self):
        self.FREQUENCY_CONFIG = FREQ_CONFIGS[self.combo_system.currentText()]
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
        # Очищаем старые графики
        for win_num in list(self.lines.keys()):
            self.plot_layout.removeWidget(self.canvases[win_num])
            self.canvases[win_num].deleteLater()
            del self.lines[win_num]
            del self.canvases[win_num]
            del self.xdata_map[win_num]

        # Создаем новые графики
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

    def start_receiving(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.is_writing = True
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.file = open(f'data/data_{current_date}.csv', 'w')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['data' + str([x]) for x in range(2048)] + ['Num Pack', 'Antenna', 'Window', 'System_type', 'Drone_type', 'Drone_is_present', 'Timestamp'])

    def stop_receiving(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.is_writing = False
        self.file.close()

    def get_data_update_plot(self, data, num_pack, num_ant, num_win):
        if self.is_writing:
            self.writer.writerow([*data, num_pack, num_ant, num_win, self.combo_system.currentText(), self.combo_drone.currentText(), int(self.drone_present_cb.isChecked()), datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')])
        if num_ant in config['antenna_list'] and num_win in config['window_list']:
            if num_win in self.lines:
                xdata = self.xdata_map[num_win]
                self.lines[num_win].set_data(xdata, data)
                ax = self.lines[num_win].axes
                ax.relim()
                ax.autoscale_view(True, True, False)
                self.canvases[num_win].draw_idle()

    def closeEvent(self, event):
        self.file.close() if self.file is not None else None
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        self.udp_worker.stop()
        self.udp_thread.quit()
        self.udp_thread.wait()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(config)
    main.show()
    sys.exit(app.exec_())