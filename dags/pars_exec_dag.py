from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import MAIN_SCRIPT_PATH, VENV_PATH

# Путь к вашему main.py
# MAIN_SCRIPT_PATH = ""
SCRIPT_DIR = os.path.dirname(MAIN_SCRIPT_PATH)

# Аргументы DAG по умолчанию
default_args = {
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# Создаем DAG
with DAG(
    dag_id='run_main_py_dag',
    default_args=default_args,
    description='Запускает main.py каждые 3 часа',
    #schedule='*/5 * * * *',  # КАЖДЫЕ 5 МИНУТ
    schedule='0 */3 * * *',  # Каждые 3 часа
    catchup=False,  # Не запускать пропущенные executions
    max_active_runs=1,
    tags=['parsing', 'scheduled'],
) as dag:

    # Задача для запуска main.py
    run_main_script = BashOperator(
        task_id='run_main_py',
        bash_command=f'bash -c "source {VENV_PATH} && cd /home/denis/vscode/test_parser/code && python main.py"',
        execution_timeout=timedelta(hours=1),  # Таймаут 1 час
        retries=2,
        retry_delay=timedelta(minutes=10),
    )

    run_main_script