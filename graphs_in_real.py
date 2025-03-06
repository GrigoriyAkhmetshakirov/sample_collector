import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import glob
import os

file_path = 'data/'
csv_files = glob.glob(os.path.join(file_path, "*.csv"))

if not csv_files:
    raise FileNotFoundError("В папке 'data/' нет CSV-файлов.")

file_path = csv_files[0]
                            
data = pd.read_csv(file_path)
print(data)

def plot_single_measurement(index, measurements, antenna_value, window_value):
    if index < len(measurements):
        signals = abs(measurements[index])
        indices = range(len(signals))
    
        average_signal = sum(signals) / len(signals)
        
        ax.clear()  
        ax.plot(indices, signals, color='green', label=f"Измерение {index+1} (Antenna {antenna_value}, Window {window_value})")
        
        #красная линия
        ax.axhline(y=average_signal, color='red', linestyle='-', label=f"Среднее значение: {average_signal:.2f}")
        
        ax.set_xlabel("Частотный индекс", fontsize=12)
        ax.set_ylabel("Сигнал антенны (модуль)", fontsize=12)
        ax.set_title("Показатели с антенны (модуль значений)", fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        
        ax.set_xlim(0, 2100)
        ax.set_ylim(0, 150)
        
        
        canvas.draw_idle() 
        
        root.after(500, lambda: plot_single_measurement(index + 1, measurements, antenna_value, window_value))
    else:
        messagebox.showinfo("Конец данных", "Все измерения отображены.")


def plot_graph():
    try:
        
        antenna_value = int(antenna_entry.get())
        window_value = int(window_entry.get())
        
        
        filtered_data = data[(data['Antenna'] == antenna_value) & (data['Window'] == window_value)]
        
        if filtered_data.empty:
            messagebox.showwarning("Нет данных", "Нет данных для заданных Antenna и Window.")
        else:
        
            measurements = [row.iloc[:-6].values for _, row in filtered_data.iterrows()]
            
            plot_single_measurement(0, measurements, antenna_value, window_value)
            
    except ValueError:
        messagebox.showerror("Ошибка ввода", "Введите корректные числовые значения.")

root = tk.Tk()
root.title("Построение графика антенны")


root.geometry("1500x1000")



tk.Label(root, text="Введите значение Antenna:", font=('Arial', 12)).grid(row=0, column=0, padx=15, pady=15, sticky='w')
antenna_entry = tk.Entry(root, font=('Arial', 12))
antenna_entry.grid(row=0, column=1, padx=15, pady=15)

tk.Label(root, text="Введите значение Window:", font=('Arial', 12)).grid(row=1, column=0, padx=15, pady=15, sticky='w')
window_entry = tk.Entry(root, font=('Arial', 12))
window_entry.grid(row=1, column=1, padx=15, pady=15)


plot_button = tk.Button(root, text="Построить график", font=('Arial', 12), bg="black", fg="white", command=plot_graph)
plot_button.grid(row=2, column=0, columnspan=2, padx=20, pady=20)


graph_frame = tk.Frame(root, width=800, height=600)
graph_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=20)


fig, ax = plt.subplots(figsize=(12, 6))

canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack()

root.mainloop()
