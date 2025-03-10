import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import glob
import os
from matplotlib.animation import FuncAnimation
import statistics
import socket

#получение имени файла куда в данный момент коллектор собирает данные
class NameClient:
    def __init__(self):
        self.host = '127.0.0.1'  # localhost
        self.port = 12345        # порт

    def get_name_from_server(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.host, self.port))

        # Отправка запроса на сервер
        request = "get_name"
        client_socket.send(request.encode('utf-8'))

        # Получение ответа от сервера
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Данные по имени файла данных от сервера: {response}")

        client_socket.close()

        return response

SHIFT=150 # параметр сдвига графика в область положительных значений.
max_Y=150
n = 50 # Окно прореживания
num = 10 #блоки для обновления
ANY_INTERVAL=2000 #обновление графиков

if __name__ == "__main__":

    client = NameClient()
    f_name = client.get_name_from_server()
    print(f"Получено имя файла данных: {f_name}")

    # Путь к папке с CSV-файлами

    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, 'data')

    csv_files = glob.glob(os.path.join(file_path, "*.csv"))

    if not csv_files:
        raise FileNotFoundError("В папке с данными нет CSV-файлов.")

    if f_name=="Not yet":
        file_path = csv_files[0]  # Выбор первого CSV-файла
    else:
        file_path = os.path.join(file_path, f_name)

    # Создание основного окна приложения
    root = tk.Tk()
    root.title("Динамика потока данных отфильтрованных по значению номер антенны ")
    root.geometry("1500x1000")  # Размер окна

    # Поля ввода значений Antenna
    tk.Label(root, text="Введите номер антенны:", font=('Arial', 12)).grid(row=0, column=0, padx=15, pady=15, sticky='w')
    antenna_entry = tk.Entry(root, font=('Arial', 12))
    antenna_entry.grid(row=0, column=1, padx=15, pady=15)
    antenna_entry.insert(tk.END, "1")  # Установка значения по умолчанию

    # Создаем области для графиков
    figs = []
    axes = []
    canvases = []
    for i in range(12):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_xlabel("Индекс", fontsize=10)
        ax.set_ylabel("Мощность сигнала", fontsize=10)
        ax.set_title(f"Окно {i+1}", fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_xlim(0, 2100)  # Обновляем пределы оси X
        ax.set_ylim(0, max_Y)  # Устанавливаем верхний предел оси Y

        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().grid(row=(i // 3) + 2, column=i % 3, padx=10, pady=10)

        figs.append(fig)
        axes.append(ax)
        canvases.append(canvas)

    # Функция для чтения данных из файла
    def read_data(window_value):
        try:
            data = pd.read_csv(file_path)
            antenna_value = int(antenna_entry.get())

            filtered_data = data[(data['Antenna'] == antenna_value) & (data['Window'] == window_value)]
            if not filtered_data.empty:
                measurements = [row.iloc[:-6].values + SHIFT for _, row in filtered_data.iterrows()]
                return measurements
            else:
                return None
        except FileNotFoundError:
            print(f"Файл {file_path} не найден.")
            return None
        except pd.errors.EmptyDataError:
            print(f"Файл {file_path} пуст.")
            return None
        except Exception as e:
            print(f"Ошибка при чтении данных: {e}")
            return None

    # Функция для обновления графиков
    def update_graphs(frame):
        for i in range(12):
            measurements = read_data(i+1)
            if measurements:

                last_blocks = measurements[-num:]
                # Если блоков меньше num, берем все доступные
                if len(last_blocks) < num:
                    last_blocks = measurements[-len(measurements):]

                # Объединяем все измерения из последних блоков
                signals = [item for block in last_blocks for item in block]

                if len(signals) > 0:

                    averaged_signals = []
                    for j in range(0, len(signals), n):
                        chunk = signals[j:j + n]
                        if len(chunk) > 0:
                            try:
                                mode_value = statistics.median(chunk) # statistics.mode(chunk)
                                averaged_signals.append(mode_value)
                            except statistics.StatisticsError:
                                # Если мода неоднозначна, берем среднее значение
                                averaged_signals.append(sum(chunk) / len(chunk))

                    axes[i].clear()  # Очищаем график перед перерисовкой
                    axes[i].plot(range(len(averaged_signals)), averaged_signals, color='green')
                    axes[i].set_xlabel("Индекс", fontsize=10)
                    axes[i].set_ylabel("Мощность сигнала", fontsize=10)
                    axes[i].set_title(f"Окно {i+1}", fontsize=12)
                    axes[i].grid(axis='y', linestyle='--', alpha=0.7)
                    axes[i].set_xlim(0, len(averaged_signals))  # Обновляем пределы оси X
                    axes[i].set_ylim(0, max_Y)  # Устанавливаем верхний предел оси Y

                    canvases[i].draw_idle()  # Обновляем график
            else:
                print(f"Нет измерений для окна {i+1}.")

    # Кнопка для применения новых фильтров
    def apply_filters():
        for ax in axes:
            ax.clear()  # Очищаем график перед перерисовкой
            ax.set_xlabel("Индекс", fontsize=10)
            ax.set_ylabel("Мощность сигнала", fontsize=10)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            ax.set_xlim(0, 2100)  # Обновляем пределы оси X
            ax.set_ylim(0,  max_Y)  # Устанавливаем верхний предел оси Y
        for canvas in canvases:
            canvas.draw_idle()  # Обновляем график

    apply_button = tk.Button(root, text="Применить фильтры", font=('Arial', 12), bg="black", fg="white", command=apply_filters)
    apply_button.grid(row=1, column=0, columnspan=3, padx=20, pady=20)

    # Запускаем анимацию
    ani = FuncAnimation(figs[0], update_graphs, interval=ANY_INTERVAL, cache_frame_data=False)

    plt.ion()
    root.mainloop()
