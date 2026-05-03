import socket
import time
from datetime import datetime
import winsound  # Только для Windows

# Конфигурация
CHECK_URL = "8.8.8.8"  # Google DNS
PORT = 53              # DNS порт
TIMEOUT = 3            # Таймаут ожидания ответа в секундах
CHECK_INTERVAL = 5     # Интервал проверки в секундах

def check_internet(host=CHECK_URL, port=PORT, timeout=TIMEOUT):
    """
    Пытается установить соединение с сервером.
    Возвращает True, если интернет есть, и False, если нет.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def log_message(message):
    """Выводит сообщение в консоль с текущим временем."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def play_sound(connected):
    """Проигрывает звук: высокий для подключения, низкий для разрыва."""
    if connected:
        winsound.Beep(1000, 200) # Частота 1000Гц, 200мс
    else:
        winsound.Beep(400, 500)  # Частота 400Гц, 500мс

def main():
    print("--- Запуск мониторинга интернета ---")
    print(f"Цель проверки: {CHECK_URL}:{PORT}")
    print("Нажмите Ctrl+C для выхода.\n")

    # Первичная проверка
    is_connected = check_internet()
    last_status = is_connected

    if is_connected:
        log_message("Статус: ПОДКЛЮЧЕНО (при запуске)")
    else:
        log_message("Статус: ОТКЛЮЧЕНО (при запуске)")

    while True:
        try:
            current_status = check_internet()

            # Если статус изменился
            if current_status != last_status:
                if current_status:
                    log_message(">>> Интернет ВОССТАНОВЛЕН! <<<")
                    play_sound(True)
                else:
                    log_message("!!! Интернет ПОТЕРЯН !!!")
                    play_sound(False)

                last_status = current_status

            # Ждем перед следующей проверкой
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nМониторинг остановлен пользователем.")
            break
        except Exception as e:
            print(f"\nПроизошла ошибка скрипта: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()