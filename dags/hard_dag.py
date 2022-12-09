import random

from datetime import datetime
import psycopg2
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from airflow.sensors.python import PythonSensor

def hello():    
    print("Hello!")
   
    
def TwoNumsPrt():
    filename=Variable.get("filename")
    with open(filename, 'a+') as f:
        f.write(f'{random.randint(0, 9)} {random.randint(0, 9)}\n')
        
def TwoNumsCalc():
    filename=Variable.get("filename")
    x=0
    output=''
    with open(filename, 'r') as f:
        for line in f:
            str_inp = line.replace('\n','').split(' ')
            if len(str_inp) >= 2:
                x += int(str_inp[0])-int(str_inp[1])
                output += f'{str_inp[0]} {str_inp[1]}\n'    
    output += f'{str(x)}\n' 
    
    with open(filename, 'w') as f:
        f.write(output)
        
#g.ii Количество строк в файле минус одна последняя - соответствует кол-ву запусков
# --как  не придумал
def check_file_count(afilename): 
    return True
    
#g.iii Финальное число рассчитано верно
def check_file_sum(afilename):
    calc=0
    linecount=0
    with open(afilename, 'r') as f:
        linecount = sum(1 for line in f)
    with open(afilename, 'r') as f:
        for i in range(0,linecount-1): 
            str_inp = f.readline().replace('\n','').split(' ')
            if len(str_inp) >= 2:  
                calc += int(str_inp[0])-int(str_inp[1])
        checksum=int(f.readline())
        print(f'calc={calc}:checksum={checksum}')        
    return(calc==checksum)        
    
      
def should_continue(**kwargs):
    filename=Variable.get("filename")  
    # g.i Файл существует    
    return os.path.exists(filename) and\
        check_file_count(filename) and\
        check_file_sum(filename)
            
# A DAG represents a workflow, a collection of tasks
default_args = {    
    "start_date": datetime(2022,12,8)    
}

with DAG(dag_id="hard_dag", default_args=default_args, schedule_interval= "2-8 20 * * *", catchup=False) as dag:    
    # Tasks are represented as operators
    bash_task = BashOperator(task_id="hello", bash_command="echo hello", do_xcom_push=False)
    python_task = PythonOperator(task_id="world", python_callable = hello)
    TwoNumsPrt_task = PythonOperator(task_id="TwoNumsPrt", python_callable = TwoNumsPrt)
    TwoNumsCalc_task = PythonOperator(task_id="TwoNumsCalc", python_callable =TwoNumsCalc)
    sens = PythonSensor(
        task_id='waiting_for_file',
        poke_interval=30,
        python_callable=lambda *args, **kwargs: should_continue()
        )
    bash_task >> python_task >> TwoNumsPrt_task >> TwoNumsCalc_task >> sens