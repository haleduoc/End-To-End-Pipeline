from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# 1. Cấu hình mặc định cho tất cả các task
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    # Tự động thử lại 1 lần nếu có sự cố mạng
    'retry_delay': timedelta(minutes=2) # Thời gian chờ trước khi thử lại
}

# Khai báo DAG
with DAG(
    dag_id='tiki_end_to_end_pipeline',
    default_args=default_args,
    description='Pipeline tự động: Cào Tiki -> Nạp Mysql -> dbt Transfrom',
    schedule_interval='0 10 * * *', # Lên lịch tự động lúc 10h sáng mỗi ngày
    catchup=False,
    tags=['ecommerce', 'tiki', 'dbt']
) as dag:
    # Task 1: Cào dữ liệu từ Tiki API
    extract_task = BashOperator(
        task_id='extract_tiki_data',
        bash_command='cd /opt/airflow/extract && python tiki.py',
    )
    # Task 2: Nạp dữ liệu thô vào Mysql
    load_task = BashOperator(
        task_id='load_to_mysql',
        bash_command='python /opt/airflow/load/load_mysql.py',
    )
    #  Task 3: chạy dbt để biến đổi dữ liệu (Staging -> Marts)
    dbt_run_task = BashOperator(
        task_id='dbt_run_transform',
        bash_command='cd /opt/airflow/transform && dbt run --profiles-dir .',
    )
    # Task 4: Chạy dbt test để kiểm tra chất lượng dữ liệu
    dbt_test_task = BashOperator(
        task_id='dbt_test_data_quality',
        bash_command='cd /opt/airflow/transform && dbt test --profiles-dir .',
    )
    
    # Xâu chuỗi luồng chạy
    extract_task >> load_task >> dbt_run_task >> dbt_test_task