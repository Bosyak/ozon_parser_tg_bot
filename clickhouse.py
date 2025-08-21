import clickhouse_connect
from typing import List
import logging

from config import CLICKHOUSE_CONFIG

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_to_clickhouse(videocards: List[dict]):
    """
    Функция для вставки данных в ClickHouse
    
    :param videocards: Список словарей с данными видеокарт
    :return: True если успешно, False если произошла ошибка
    """
    try:
        # Подключение к ClickHouse
        connect_kwargs = {
            'host': CLICKHOUSE_CONFIG['host'],
            'port': CLICKHOUSE_CONFIG['port'],
            'database': CLICKHOUSE_CONFIG['database']
        }
        
        if CLICKHOUSE_CONFIG.get('username'):
            connect_kwargs['username'] = CLICKHOUSE_CONFIG['username']
        if CLICKHOUSE_CONFIG.get('password'):
            connect_kwargs['password'] = CLICKHOUSE_CONFIG['password']
        
        client = clickhouse_connect.get_client(**connect_kwargs)
        logger.info(f"Подключение к ClickHouse успешно: {CLICKHOUSE_CONFIG['host']}:{CLICKHOUSE_CONFIG['port']}/{CLICKHOUSE_CONFIG['database']}")
    except Exception as e:
        logger.error(f"Ошибка подключения к ClickHouse: {e}")
        return False
    
    try:
        if not videocards:
            logger.info("Нет данных для вставки")
            return True
        
        # Вставляем данные      
        try:
            insert_query = f"""
            INSERT INTO {CLICKHOUSE_CONFIG['table']} (event_time, product_id, title, description, card_price, offers_price, offers_priceCurrency, sku, rating, product_url)
            VALUES (now(), \'{videocards['product_id']}\', \'{videocards['title']}\', \'{videocards['description']}\', {videocards['card_price']}, {videocards['offers_price']}, \'{videocards['offers_priceCurrency']}\', \'{videocards['sku']}\', {videocards['rating']}, \'{videocards['product_url']}\')
            """
            client.command(insert_query)
        except Exception as e:
            logger.error(f"Ошибка при вставке записи: {e}.")
        
        logger.info(f"Успешно вставлено {len(videocards)} записей в ClickHouse")
        return True
        z
    except Exception as e:
        logger.error(f"Ошибка при работе с ClickHouse: {e}")
        return False
    finally:
        if client:
            client.close()
            logger.info("Соединение с ClickHouse закрыто")          