import random

from datetime import datetime
import psycopg2
import numpy as np
import pandas as pd
import csv

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from airflow.operators.email_operator import EmailOperator
from airflow.hooks.base import BaseHook
from airflow.sensors.sql import SqlSensor

def get_con_creditials(conn_id) -> BaseHook.get_connection:
    conn = BaseHook.get_connection(conn_id)
    return conn

#pg_hostname = 'host.docker.internal'
#pg_port = '5430'
#pg_username = 'postgres'
#pg_pass = 'postgres'
#pg_db = 'test'

def hello():
    print("Hello!")

def TwoNumsPrt():
    print(random.randint(0, 9))
    print(random.randint(0, 9))
    
def connect_to_psql(**kwargs):
    ti = kwargs['ti']
    conn_id=Variable.get("conn_id")
    pg_conn = get_con_creditials(conn_id)
    pg_hostname, pg_port, pg_username, pg_pass, pg_db = pg_conn.host, pg_conn.port, \
        pg_conn.login, pg_conn.password, pg_conn.schema
    ti.xcom_push(value=[pg_hostname, pg_port, pg_username, pg_pass, pg_db], key='conn_to_airflow')
    conn = psycopg2.connect(host=pg_hostname, port=pg_port, user=pg_username, password=pg_pass, database=pg_db)
    cursor = conn.cursor()

    #cursor.execute("CREATE TABLE test_table (id serial PRIMARY KEY, num integer, data varchar);")
    cursor.execute("INSERT INTO test_table (num, data) VALUES (%s, %s)",(100, "abc'def"))
    
    #cursor.fetchall()
    conn.commit()

    cursor.close()
    conn.close()

def read_from_psql(**kwargs):
    ti = kwargs['ti']
    #conn_id=Variable.get("conn_id")
    #pg_conn = get_con_creditials(conn_id)
    #pg.conn = ti.xcom_pull(key='conn_to_airflow', task_id ='conn_to_psql')
    #pg_hostname, pg_port, pg_username, pg_pass, pg_db = pg_conn.host, pg_conn.port, \
    #                                                    pg_conn.login, pg_conn.password, pg_conn.schema

    pg_hostname, pg_port, pg_username, pg_pass, pg_db =ti.xcom_pull(key='conn_to_airflow', task_ids ='conn_to_psql')
    conn = psycopg2.connect(host=pg_hostname, port=pg_port, user=pg_username, password=pg_pass, database=pg_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_table;")
    print(cursor.fetchone())
    
    cursor.close()
    conn.close()
    
def sum1forline(filename):
    with open(filename) as f:
        return sum(1 for line in f)
        
def FileLineCount (**kwargs):
    ti = kwargs['ti']
    filename = 'cities.csv'
    #path = '/home/airflow/'
    fullFileName = Variable.get('fullfilename')
    #linecount = pd.read_csv(fullFileName, delimiter=',').shape[0]
    with open(fullFileName) as f:
         linecount = sum(1 for line in f)
    ti.xcom_push(value=linecount, key='linecount')

def readFileLineCount(**kwargs):
    ti = kwargs['ti']
    linecount = ti.xcom_pull(key='linecount', task_ids ='FileLineCount')
    fullFileName = Variable.get('fullfilename')
    with open(fullFileName+".tmp","w") as ftemp:
      with open(fullFileName) as f:
         for line in f :
             ftemp.write(line.rstrip() + ','+str(linecount)+'\n')
             linecount-=1
    f.close
    ftemp.close

    
# A DAG represents a workflow, a collection of tasks
with DAG(dag_id="test_dag", start_date=datetime(2022, 11, 30), schedule="0 0 * * *") as dag:    
    # Tasks are represented as operators
    bash_task = BashOperator(task_id="hello", bash_command="echo hello", do_xcom_push=False)
    python_task = PythonOperator(task_id="world", python_callable = hello)
    TwoNumsPrt_task = PythonOperator(task_id="TwoNumsPrt", python_callable = TwoNumsPrt)
    
    #conn_to_psql_tsk = PythonOperator(task_id="conn_to_psql", python_callable = connect_to_psql)
    #read_from_psql_tsk = PythonOperator(task_id="read_from_psql", python_callable = read_from_psql)
    #FileLineCount_tsk =PythonOperator(task_id="FileLineCount", python_callable = FileLineCount)
    #ReadFileLineCount_tsk = PythonOperator(task_id="ReadFileLineCount", python_callable=readFileLineCount)
    #sql_sensor = SqlSensor(
    #    task_id='limits_test',
    #    conn_id=Variable.get("conn_id"),
    #    sql="SELECT * FROM test_table"
    #)
    # Set dependencies between tasks
    #bash_task >> python_task >> conn_to_psql_tsk >> read_from_psql_tsk
    #conn_to_psql_tsk >> read_from_psql_tsk>> sql_sensor>> bash_task
    #FileLineCount_tsk >> ReadFileLineCount_tsk
    bash_task >> python_task >> TwoNumsPrt_task