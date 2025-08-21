from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import json
import time
import re

def calculate_product_info(driver, url):
    try:
        # Сохраняем текущую вкладку
        original_window = driver.current_window_handle
        
        # Открываем новую вкладку
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        
        # JSON-страница
        url_prod = "https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=" + url
        driver.get(url_prod)
        time.sleep(1.0)

        response_content = driver.execute_script("return document.body ? document.body.innerText : '';") or ""
        if len(response_content) < 1000:
            response_content = driver.page_source or ""

        product_id = title = description = card_price = offers_price = offers_priceCurrency = sku = rating = ""

        # 1) TITLE из seo
        m_title = re.search(r'"seo"\s*:\s*\{\s*"title"\s*:\s*"([^"]+)"', response_content, re.DOTALL)
        if m_title:
            title = m_title.group(1)
            title = title.split('купить')
            title = title[0]
            title = str(title)

        # 2) Product в JSON-LD, лежащем в "script":[{"innerHTML":"..."}]
        #    ВАЖНО: шаблон, корректно учитывающий экранированные кавычки
        inner_pat = re.compile(r'"innerHTML"\s*:\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)

        pi = re.search(r'product_id=(\d+)', response_content, re.DOTALL)
        if pi:
            product_id = pi.group(1)
        rt = re.search(r'graphicRating\\",\\"text\\":\\"(\d+\.\d+|\d+)', response_content, re.DOTALL)
        if rt:
            rating = rt.group(1)
        cp = re.search(r'cardPrice\\":\\"(\d+\s+\d+\s+\d+|\d+\s+\d+|\d+)', response_content, re.DOTALL)
        if cp:
            card_price = cp.group(1)
            card_price = card_price = ''.join(char for char in card_price if not char.isspace())
            

        found = False
        for m in inner_pat.finditer(response_content):
            raw = m.group(1)
            try:
                unescaped = json.loads(f'"{raw}"')   # снять экранирование строки
                data = json.loads(unescaped)         # разобрать как JSON
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and "@graph" in data and isinstance(data["@graph"], list):
                for node in data["@graph"]:
                    if isinstance(node, dict) and node.get("@type") == "Product":
                        data = node
                        break

            if not isinstance(data, dict):
                continue

            if data.get("@type") == "Product" or "offers" in data or "sku" in data:
                description = (data.get("description") or "").replace("\n", "\\n")
                offers = data.get("offers") or {}
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                if isinstance(offers, dict):
                    if offers.get("price") is not None:
                        offers_price = str(offers.get("price", ""))
                    offers_priceCurrency = offers.get("priceCurrency", "") or ""

            sku = str(data.get("sku", ""))

        # 4) Выводим ВСЁ
        print("product_id:", product_id)
        print("title:", title)
        print("description:", description)
        print("card_price:", card_price)
        print("offers_price:", offers_price)
        print("offers_priceCurrency:", offers_priceCurrency)
        print("sku:", sku)
        print("rating:", rating)

    finally:
        time.sleep(2)
        driver.close()
        driver.switch_to.window(original_window)
    return product_id, title, description, card_price, offers_price, offers_priceCurrency, sku, rating

if __name__ == "__main__":
    print(card_info)
    