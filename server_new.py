import socket
import struct
import time
import numpy as np

UDP_IP = "127.0.0.1"
UDP_PORT = 49049
SEND_INTERVAL = 0.05  # Интервал отправки
num_ant_qnt=8
num_win_qnt=12

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

num_pack = 0
num_ant = 1
num_win = 1


def generate_packet(num_ant, num_win):
    global num_pack, E, S

    # Изменяем E и S с периодом M пакетов
    M=200+2*num_ant+3*num_win
    U=int(M/2)
    if num_pack % M < U:
        E = -90+ num_ant  # Среднее
        S = 5  # Дисперсия
    else:
        E = -80 +2*num_ant # Среднее
        S = 15  # Дисперсия

    sigma = np.sqrt(S)  # Стандартное отклонение

    # Генерируем гауссовский шум
    values = np.random.normal(E, sigma, 2048)

    # Ограничиваем значения в диапазоне [-100, 0]
    values = np.clip(values, -100, 0)

    num_pack += 1
    diag = 1

    packed_data = struct.pack('2048f I B B B', *values, num_pack, num_ant, num_win, diag)

    return packed_data


try:
    print(f'Отправка UDP-пакетов на {UDP_IP}:{UDP_PORT}...')

    while True:
        packet = generate_packet(num_ant, num_win)
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        print(f'Отправлен пакет {num_pack} (num_ant={num_ant}, num_win={num_win})')

        # Обновляем num_win и num_ant
        num_win += 1
        if num_win > num_win_qnt:
            num_win = 1
            num_ant += 1
            if num_ant > num_ant_qnt:
                num_ant = 1  # Возвращаемся к началу цикла

        time.sleep(SEND_INTERVAL)

except KeyboardInterrupt:
    print('\nПередача остановлена.')
except socket.error as e:
    print(f'Сетевая ошибка: {e}')
except Exception as e:
    print(f'Произошла ошибка: {e}')

finally:
    sock.close()
