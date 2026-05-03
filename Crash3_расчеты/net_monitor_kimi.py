import socket
import requests
import time
from urllib.error import URLError
from datetime import datetime

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Проверка подключения к интернету через DNS-запрос
    
    Args:
        host: DNS сервер (по умолчанию Google DNS)
        port: Порт (53 для DNS)
        timeout: Таймаут в секундах
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(f"Socket error: {ex}")
        return False

def check_http_connection(url="http://www.google.com", timeout=5):
    """
    Проверка HTTP соединения
    
    Args:
        url: URL для проверки
        timeout: Таймаут в секундах
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

def monitor_connection(poll_interval=10):
    """
    Мониторинг соединения с выводом статуса
    
    Args:
        poll_interval: Интервал между проверками в секундах
    """
    print("=== Мониторинг подключения к интернету ===")
    print(f"Проверка каждые {poll_interval} секунд (Ctrl+C для остановки)\n")
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Проверяем оба способа
        dns_ok = check_internet_connection()
        http_ok = check_http_connection()
        
        status = "✅ ОНЛАЙН" if (dns_ok and http_ok) else "❌ ОФФЛАЙН"
        
        print(f"[{timestamp}] {status} (DNS: {'OK' if dns_ok else 'FAIL'}, HTTP: {'OK' if http_ok else 'FAIL'})")
        
        time.sleep(poll_interval)

if __name__ == "__main__":
    # Быстрая проверка
    print("Быстрая проверка подключения...")
    if check_internet_connection():
        print("✅ Подключение к интернету активно!")
    else:
        print("❌ Нет подключения к интернету!")
    
    # Проверка HTTP
    print("\nПроверка HTTP соединения...")
    if check_http_connection():
        print("✅ HTTP соединение работает!")
    else:
        print("❌ HTTP соединение не работает!")
    
    # Запуск мониторинга
    print("\n" + "="*50)
    try:
        monitor_connection(poll_interval=15)  # Проверка каждые 15 секунд
    except KeyboardInterrupt:
        print("\n\nМониторинг остановлен пользователем.")
