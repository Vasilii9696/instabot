import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager as CM
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service


# Сохранение учетных данных (логин и пароль) в файл
def save_credentials(username, password):
    with open('credentials.txt', 'w') as file:
        file.write(f"{username}\n{password}")


# Загрузка учетных данных из файла, если файл существует
def load_credentials():
    if not os.path.exists('credentials.txt'):
        return None

    with open('credentials.txt', 'r') as file:
        lines = file.readlines()
        if len(lines) >= 2:
            return lines[0].strip(), lines[1].strip()

    return None


# Запрос логина и пароля от пользователя и сохранение их в файл
def prompt_credentials():
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    save_credentials(username, password)
    return username, password


# Функция для авторизации в Instagram через Selenium
def login(bot, username, password):
    # Переход на страницу входа Instagram
    bot.get('https://www.instagram.com/accounts/login/')
    time.sleep(1)

    # Проверка необходимости принять куки
    try:
        element = bot.find_element(By.XPATH, "/html/body/div[4]/div/div/div[3]/div[2]/button")
        element.click()
    except NoSuchElementException:
        print("[Info] - Instagram did not require to accept cookies this time.")

    print("[Info] - Logging in...")

    # Ожидание загрузки полей ввода для логина и пароля
    username_input = WebDriverWait(bot, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password_input = WebDriverWait(bot, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))

    # Очистка полей и ввод данных
    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)

    # Нажатие кнопки входа
    login_button = WebDriverWait(bot, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    login_button.click()

    # Ожидание, чтобы убедиться, что авторизация прошла успешно
    time.sleep(10)


# Функция для сбора списка подписчиков пользователя в Instagram
def scrape_followers(bot, username, user_input):
    # Переход на страницу профиля пользователя
    bot.get(f'https://www.instagram.com/{username}/')
    time.sleep(3.5)

    # Ожидание появления ссылки на подписчиков и нажатие на нее
    WebDriverWait(bot, TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers')]"))).click()
    time.sleep(2)
    print(f"[Info] - Scraping followers for {username}...")

    users = set()

    # Пока количество собранных пользователей не достигнет нужного, продолжаем скроллить и собирать ссылки
    while len(users) < user_input:
        followers = bot.find_elements(By.XPATH, "//a[contains(@href, '/')]")

        for i in followers:
            if i.get_attribute('href'):
                users.add(i.get_attribute('href').split("/")[3])
            else:
                continue

        # Скроллим вниз, чтобы загрузить больше подписчиков
        ActionChains(bot).send_keys(Keys.END).perform()
        time.sleep(1)

    # Ограничиваем список собранных пользователей до нужного числа
    users = list(users)[:user_input]

    print(f"[Info] - Saving followers for {username}...")

    # Сохранение списка подписчиков в файл
    with open(f'{username}_followers.txt', 'a') as file:
        file.write('\n'.join(users) + "\n")


# Основная функция для запуска скрипта
def scrape():
    # Загрузка учетных данных
    credentials = load_credentials()

    # Если учетные данные не найдены, запрашиваем их у пользователя
    if credentials is None:
        username, password = prompt_credentials()
    else:
        username, password = credentials

    # Запрашиваем количество подписчиков для сбора
    user_input = int(input('[Required] - How many followers do you want to scrape (100-2000 recommended): '))

    # Запрашиваем список пользователей для сбора подписчиков
    usernames = input("Enter the Instagram usernames you want to scrape (separated by commas): ").split(",")

    # Настройка Selenium веб-драйвера Chrome
    service = Service()
    options = webdriver.ChromeOptions()
    # Можно раскомментировать следующую строку для работы в фоновом режиме (без отображения браузера)
    # options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument("--log-level=3")

    # Настройка эмуляции мобильного устройства
    mobile_emulation = {
        "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/90.0.1025.166 Mobile Safari/535.19"
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)

    # Запуск браузера
    bot = webdriver.Chrome(service=service, options=options)
    bot.set_page_load_timeout(60)  # Установка тайм-аута для загрузки страницы

    # Вход в аккаунт Instagram
    login(bot, username, password)

    # Цикл по каждому пользователю для сбора подписчиков
    for user in usernames:
        user = user.strip()
        scrape_followers(bot, user, user_input)

    # Закрытие браузера
    bot.quit()


# Запуск скрипта
if __name__ == '__main__':
    TIMEOUT = 60
    scrape()
