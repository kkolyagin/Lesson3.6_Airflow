import random

from datetime import datetime
import psycopg2

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator

def hello():
    print("Hello!")

def TwoNumsPrt():
    filename='/home/airflow/test.txt'
    with open(filename, 'a+') as f:
        f.write(f'{random.randint(0, 9)} {random.randint(0, 9)}\n')
        
def TwoNumsCalc():
    filename='/home/airflow/test.txt'
    x=0
    output=''
    with open(filename, 'r') as f:
        for line in f:
            str_inp = line.replace('\n','').split(' ')
            if len(str_inp) >= 2:
                x += int(str_inp[0])-int(str_inp[1])
                output += f'{str_inp[0]} {str_inp[1]} {str(x)}\n'    
    print(output)            
    with open(filename, 'r+') as f:
        f.write(output)
    
# A DAG represents a workflow, a collection of tasks
with DAG(dag_id="light_dag", start_date=datetime(2022, 12, 5), schedule="0-5 9 5 12 *") as dag:    
    # Tasks are represented as operators
    bash_task = BashOperator(task_id="hello", bash_command="echo hello", do_xcom_push=False)
    python_task = PythonOperator(task_id="world", python_callable = hello)
    TwoNumsPrt_task = PythonOperator(task_id="TwoNumsPrt", python_callable = TwoNumsPrt)
    TwoNumsCalc_task = PythonOperator(task_id="TwoNumsCalc", python_callable =TwoNumsCalc)
    
    bash_task >> python_task >> TwoNumsPrt_task >> TwoNumsCalc_task