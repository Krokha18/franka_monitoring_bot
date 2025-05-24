import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service # Додано


def init_webdriver():
    # Setup selenium
    chrome_options = Options()
    chrome_options.binary_location = os.getenv("CHROMIUM_BIN","/usr/bin/chromium-browser")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    webdriver_service = Service(os.getenv("CHROMEDRIVER_BIN",'/usr/bin/chromedriver'))
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    return driver, wait
