from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from bs4 import BeautifulSoup


from get_product_info import calculate_product_info
from clickhouse import insert_to_clickhouse

import time
import json

def init_webdriver():
    #options.add_argument(f"--user-data-dir={temp_dir}")
    #options.add_argument("--headless")  # ✅ Без GUI
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    stealth(driver,
            languages=["ru-RU", "ru"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    driver.maximize_window()
    return driver

def scrolldown(driver, deep):
    for _ in range(deep):
        driver.execute_script('window.scrollBy(0, 500)')
        time.sleep(0.3)    

def get_searchpage_cards(driver, url, all_cards = []):
    driver.get(url)
    scrolldown(driver, 6)
    print('пролистал вниз')
    search_page_html = BeautifulSoup(driver.page_source, "html.parser")
    print('запустил суп')
    content = search_page_html.find("div", {"id": "layoutPage"})
    print('нашел layoutPage')
    content = content.find("div")
    print('нашел div')
    content = content.find("div")
    content = content.find("div")
    content = content.find("div", {"class": "container"}) # container c
    target_div = content.find("div", {"data-widget": "tileGridDesktop"})
    print(str(target_div)[:100])
    print('нашел карточки')
    cards = target_div.find_all('div', attrs={'data-index': True})
    cards_in_page = list()
    for card in cards:
        card_url = card.find("a", href=True)["href"]
        print('card_url - ', card_url)
        card_name = card.find("span", {"class": "tsBody500Medium"}).contents[0]
        print('card_name - ', card_name)
        product_url = "https://ozon.ru" + card_url
        #product_id, title, description, offers_price, offers_priceCurrency, sku
        product_id, title, description, card_price, offers_price, offers_priceCurrency, sku, rating = calculate_product_info(driver, card_url)
        card_info = {"product_id": product_id,
                     "title": title,
                     "description": description,
                     "card_price": card_price,
                     "offers_price": offers_price,
                     "offers_priceCurrency": offers_priceCurrency,
                     "sku": sku,
                     "rating": rating,
                     "product_url": product_url
                    }
        insert_to_clickhouse(card_info)
        cards_in_page.append(card_info)
        print(product_id, "- DONE")

    content_with_next = [div for div in content.find_all("a", href=True) if "Дальше" in str(div)]
    if not content_with_next:
        return cards_in_page
    else:
        next_page_url = "https://www.ozon.ru" + content_with_next[0]["href"]
        all_cards.extend(get_searchpage_cards(driver, next_page_url, cards_in_page))
        return all_cards


if __name__ == "__main__":
    url_ozon = "https://www.ozon.ru"

    driver = init_webdriver()

    search_list = []#["видеокарта+5070"]
    try:
        with open('список для поиска.txt', 'r', encoding='utf-8') as file:
            for line in file:
                # Убираем символы переноса строки и добавляем в список
                search_list.append(line.strip())
                print(search_list)
    except FileNotFoundError:
        print("Файл не найден!")
        search_list = []  # Инициализируем пустым списком
    end_list = list()

    for search_tag in search_list:
        url_search = f"https://www.ozon.ru/search/?text={search_tag}&from_global=true"

        try:
            print('пытаюсь найти карточки')
            search_cards = get_searchpage_cards(driver, url_search)
            print("Я успешно нашёл", len(search_cards), "по поиску", search_tag)
            end_list.append(search_tag)
        except:
            print("Я упал на", search_tag)
    print(end_list)
    time.sleep(0.3)
    driver.quit()