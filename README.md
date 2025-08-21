# Парсер сайта ozon.ru и тг бот

### Структура проекта:
**парсер** - main.py > get_product_info.py > clickhouse.py
**тг бот** - tg_bot.py
**шедулер** - airflow - pars_exec_dag.py
**Создаем виртуальное окружение и активируем его. Устанавливаем нужные библиотеки для проекта**

pip install beautifulsoup4
pip install curl_cffi
pip install selenium
pip install selenium-stealth
pip install webdriver-manager
pip install --upgrade selenium webdriver-manager
pip install aiogram
pip install clickhouse_connect

**Также нам понадобится файл config.py:**

CLICKHOUSE_CONFIG = {
    'host': 'localhost',
    'port': 8123,  # HTTP-порт
    'database': 'mag_db',
    'table': 'ozon_stuff',
    'username': '',
    'password': ''
}

API_TOKEN = '...'

MAIN_SCRIPT_PATH = ".../main.py"

VENV_PATH = ".../bin/activate"

**Устанавливаем airflow standalone. Это самый простой способ запуска airflow, т. к. для нашей задачи этого достаточно.**

pip install apache-airflow
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__DAGS_FOLDER=/home/denis/vscode/test_parser/code/dags


**В терминале появится логин и пароль для входа в airflow**

**Устанавливаем clickhouse сервер и клиент**

sudo apt-get install -y apt-transport-https ca-certificates dirmngr
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv E0C56BD4

echo "deb https://packages.clickhouse.com/deb stable main" | sudo tee \
    /etc/apt/sources.list.d/clickhouse.list

sudo apt-get install -y clickhouse-server clickhouse-client

**Запуск сервера**

sudo service clickhouse-server start

**После нужно создать бд и таблицу для хранения результатов парсинга**

cat <<END | clickhouse-client --multiline
CREATE DATABASE mag_db;
END

cat <<END | clickhouse-client --multiline
CREATE TABLE mag_db.ozon_stuff
(
    event_time DateTime('Europe/Moscow'),
    product_id String,    
    title String,
    description String,
    card_price UInt32,
    offers_price UInt32,
    offers_priceCurrency String,
    sku String,
    rating Float32,
    product_url String
)
ENGINE = MergeTree()
ORDER BY (event_time, product_id, title)
END

**Всё готово, осталось запустить airflow**

airflow standalone

**И нужно запустить телеграм бот**

python tg_bot.py
