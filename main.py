#!/usr/bin/env python3

import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging
from notion_client import Client

logging.basicConfig(filename='crypto_price_update.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

loggers = ['requests', 'notion_client']
for logger_name in loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)


def get_stock_price(ticker):
    driver = None
    try:
        url_nas = 'https://live.euronext.com/en/product/equities/no0010196140-xosl'
        url_nom = 'https://live.euronext.com/en/product/equities/NO0013162693-XOAS'
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        if ticker == "NAS":
            driver.get(url_nas)
        else:
            driver.get(url_nom)
        time.sleep(5)
        try:
            price_element = driver.find_element(By.ID, 'header-instrument-price')
            if price_element:
                return round(float(price_element.text), 3)
        except Exception as exception:
            logging.error(f"During fetch a price element from the website an error occurred. Exception: {exception}")
            return None
    except Exception as exception:
        logging.error(f"An error with driver occurred: {exception}")
    finally:
        if driver:
            driver.quit()


def get_price(api_key, ticker):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={ticker}USDT"
    headers = {'X-MBX-APIKEY': api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return float(data['price'])
    else:
        logging.error(f"Failed to retrieve data for {ticker}: Status code {response.status_code}")
        return None


def update_notion_price(notion_token, database_id, target_ticker, price):
    notion = Client(auth=notion_token)
    try:
        query_response = notion.databases.query(
            database_id=database_id,
            filter={"property": "Ticker", "rich_text": {"equals": target_ticker}}
        )
        green_select_up = {'id': '82d04a47-0903-4726-8469-c0aa3b815746', 'name': 'up', 'color': 'green'}
        red_select_down = {'id': '0e911ead-f479-498a-a471-a1fe399a103f', 'name': 'down', 'color': 'red'}


        for page in query_response['results']:
            ticker_text = page['properties']['Ticker']['rich_text'][0]['plain_text']
            if ticker_text == target_ticker:
                page_id = page['id']
                initial_investment = page['properties']['Initial Investment']['formula']['number']
                current_value = page['properties']['Current Value']['formula']['number']
                up_select = green_select_up if current_value > initial_investment else red_select_down
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        "Current Price": {"number": price},
                        "up": {"select": up_select}
                    }
                )
                logging.info(
                    f"Ticker: {target_ticker} | Price: ${price} | Current Value: ${current_value} | Initial Value: ${initial_investment}")

                return
        logging.warning(f"No exact match found for ticker {target_ticker}")
    except Exception as e:
        logging.error(f"An error occurred while updating Notion: {str(e)}")


# Configurable parameters

api_key = os.getenv("BINANCE_API_KEY")
notion_token = os.getenv("CRYPTO_PRICE_UPDATER_NOTION")
database_id = os.getenv("NOTION_CRYPTO_DATABASE_API")

tickers = ['MDT', 'OGN', 'NAS', 'NOM']

for ticker in tickers:
    if ticker == 'NAS' or ticker == 'NOM':
        price = get_stock_price(ticker)
    else:
        price = get_price(api_key, ticker)
    if price is not None:
        update_notion_price(notion_token, database_id, ticker, price)
    else:
        logging.info(f"Could not fetch price for {ticker}, skipping Notion update.")

