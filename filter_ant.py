import pandas as pd

file_path = 'data/data_2025-03-06_16-16-37.csv'
data = pd.read_csv(file_path)

if 'Antenna' not in data.columns or 'Window' not in data.columns:
    print("Ошибка: В файле нет столбцов 'Antenna' или 'Window'")
else:

    antenna_value = input("Введите значение Antenna: ")
    window_value = input("Введите значение Window: ")

    filtered_data = data[(data['Antenna'] == int(antenna_value)) & (data['Window'] == int(window_value))]

    sorted_data = filtered_data.sort_values(by=['Antenna', 'Window'])

    print(sorted_data)

    sorted_data.to_csv("data/filtered_data.csv", index=False)
    print("Фильтрованные данные сохранены в 'filtered_data.csv'")
