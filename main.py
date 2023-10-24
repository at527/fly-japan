from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


def search_one_way(departure_port, arrival_port, date):
    return 0


def search_round_trip(departure_port, arrival_port, departure_date, return_date):
    return 0


def main():
    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://www.selenium.dev/selenium/web/web-form.html")
    
    
    driver.implicitly_wait(0.5)

    driver.quit()

    return 0


if __name__ == "__main__":
    main()
