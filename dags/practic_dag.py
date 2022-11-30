from datetime import datetime
import psycopg2

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from airflow.operators.email_operator import EmailOperator

pg_hostname = 'host.docker.internal'
pg_port = '5430'
pg_username = 'postgres'
pg_pass = 'postgres'
pg_db = 'test'

def hello():
    print("Hello!")

def connect_to_psql():
    conn = psycopg2.connect(host=pg_hostname, port=pg_port, user=pg_username, password=pg_pass, database=pg_db)
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE test_table (id serial PRIMARY KEY, num integer, data varchar);")
    cursor.execute("INSERT INTO test_table (num, data) VALUES (%s, %s)",(100, "abc'def"))
    
    #cursor.fetchall()
    conn.commit()

    cursor.close()
    conn.close()

def read_from_psql():
    conn = psycopg2.connect(host=pg_hostname, port=pg_port, user=pg_username, password=pg_pass, database=pg_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_table;")
    print(cursor.fetchone())
    
    cursor.close()
    conn.close()
    
def sum1forline(filename):
    with open(filename) as f:
        return sum(1 for line in f)
        
def FileLineCount ():
    filename = 'cities.csv'
    path = '/home/airflow/'
    with open(path+filename) as f:
         linecount = sum(1 for line in f) 
    print(linecount)
         
# A DAG represents a workflow, a collection of tasks
with DAG(dag_id="test_dag", start_date=datetime(2022, 11, 30), schedule="0 0 * * *") as dag:    
    # Tasks are represented as operators
    #bash_task = BashOperator(task_id="hello", bash_command="echo hello")
    #python_task = PythonOperator(task_id="world", python_callable = hello)
    #conn_to_psql_tsk = PythonOperator(task_id="conn_to_psql", python_callable = connect_to_psql)
    #read_from_psql_tsk = PythonOperator(task_id="read_from_psql", python_callable = read_from_psql)
    FileLineCount_tsk =PythonOperator(task_id="FileLineCount", python_callable = FileLineCount)

    # Set dependencies between tasks
    #bash_task >> python_task >> conn_to_psql_tsk >> read_from_psql_tsk
    FileLineCount_tsk