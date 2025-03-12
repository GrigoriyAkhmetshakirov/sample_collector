import matplotlib.pyplot as plt
import pandas as pd

# Включаем интерактивный режим
plt.ion()

data = pd.read_csv('data/data_2025-03-12_14-40-21.csv')
selected_data = data[(data['Window'] == 1) & (data['Antenna'] == 1)]
filtered_data = selected_data.drop(columns=['Num Pack', 'Antenna', 'Window', 'Diag', 'System_type', 'Drone_type', 'Timestamp'])

fig, ax = plt.subplots()

for i in range(len(data)):
    ax.clear() 
    row = filtered_data.iloc[i]
    if row.empty:
        print(f"Строка {i} пустая. Пропускаем.")
        continue

    row.plot(ax=ax)
    ax.set_title(f'Row {i}')
    plt.draw()
    plt.pause(0.1)

plt.ioff()
plt.show()