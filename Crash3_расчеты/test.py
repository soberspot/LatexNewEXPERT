from selenium import webdriver
from selenium.webdriver.common.by import By
import time

art = "S18D6300010DY"
driver = webdriver.Chrome()
driver.get("https://idriver.by")
time.sleep(2)
search = driver.find_element(By.NAME, "keyword")   # имя поля на idriver
search.clear()
search.send_keys(art + "\n")
time.sleep(4)
print(driver.current_url)          # какая сейчас страница
print(driver.title)                # заголовок
cards = driver.find_elements(By.CSS_SELECTOR, "div.product-item")
print("найдено карточек:", len(cards))
driver.quit()