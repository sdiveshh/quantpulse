from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def _prices():
    from stream_processor import run
    run(do_prices=True, do_news=False)


def _news():
    from stream_processor import run
    run(do_prices=False, do_news=True)


def _transform():
    from transform_market_data import run
    run()


DEFAULT_ARGS = {"retries": 2, "retry_delay": timedelta(minutes=2)}

with DAG(
    dag_id="quantpulse_market_pipeline",
    description="Ingest prices every 15 minutes, then validate and build features",
    start_date=datetime(2026, 10, 1),
    schedule="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["quantpulse"],
) as prices_dag:
    ingest_prices = PythonOperator(task_id="ingest_prices", python_callable=_prices)
    transform = PythonOperator(task_id="validate_and_transform", python_callable=_transform)
    ingest_prices >> transform

with DAG(
    dag_id="quantpulse_news_pipeline",
    description="Ingest news every 6 hours to stay inside the NewsAPI free limit",
    start_date=datetime(2026, 10, 1),
    schedule="0 */6 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["quantpulse"],
) as news_dag:
    PythonOperator(task_id="ingest_news", python_callable=_news)