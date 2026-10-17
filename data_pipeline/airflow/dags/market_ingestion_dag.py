from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def _ingest():
    from stream_processor import run
    run()


def _transform():
    from transform_market_data import run
    run()


with DAG(
    dag_id="quantpulse_market_pipeline",
    description="Ingest prices and news, then build features",
    start_date=datetime(2026, 10, 1),
    schedule="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["quantpulse"],
) as dag:
    ingest = PythonOperator(task_id="ingest_prices_and_news", python_callable=_ingest)
    transform = PythonOperator(task_id="validate_and_transform", python_callable=_transform)
    ingest >> transform