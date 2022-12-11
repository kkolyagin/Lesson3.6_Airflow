import random

from datetime import datetime
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from airflow.sensors.python import PythonSensor
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

#TASK python_task - пример PythonOperator, печатает Hello!###############
def hello():    
    print("Hello!")   

#TASK TwoNumsPrt_task - генерирует два произвольных числа и записываeт в текстовый файл – через пробел. ###
#каждые новые два числа записываются новой строки не затирая предыдущие
def TwoNumsPrt():
    filename=Variable.get("filename")
    with open(filename, 'a+') as f:
        f.write(f'{random.randint(0, 9)} {random.randint(0, 9)}\n')
        
#TASK TwoNumsCalc_task - подключается к файлу и вычисляет сумму всех чисел из первой колонки, ###
#затем сумму всех чисел из второй колонки и рассчитывает разность полученных сумм.
#Вычисленная разность записывается в конец того же файла, не затирая его содержимого.
#При каждой новой записи произвольных чисел в конец файла, вычисленная сумма затирается.
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
        
#TASK sens - Процедуры для проверка файла ############        
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
        
#TASK select_next_task - ветление ##########
def select_next_task():    
    linecount=0
    filename=Variable.get("filename")   
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            linecount = sum(1 for line in f)
        if linecount > 0:
            return 'file_exist'
    else:
        return 'error_task'       

#TASK error_task##############        
def file_error():
    filename=Variable.get("filename")   
    print(f'{filename} not exists or empty')

#TASK file_exist #############
#Читает файл и создает таблицу аналогичной структуры в Postgres и наполняет ее данными из файла(за иск. последнего числа)    
def make_table(**kwargs):
    ti = kwargs['ti']
    conn_id=Variable.get("conn_id")
    hook = PostgresHook(postgres_conn_id=conn_id)
    query='CREATE TABLE if not exists rnd_table (id serial PRIMARY KEY, value_1 integer, value_2 integer)'
    hook.run(sql=query) 
    hook.run(sql='truncate rnd_table') #Очищаю таблицу
    filename=Variable.get("filename")
    calc=0
    linecount=0
    with open(filename, 'r') as f:
        linecount = sum(1 for line in f)
    with open(filename, 'r') as f:
        for i in range(0,linecount-1): 
            str_inp = f.readline().replace('\n','').split(' ')
            if len(str_inp) >= 2:  
                query = f'INSERT INTO rnd_table (value_1,value_2) VALUES ({int(str_inp[0])}, {int(str_inp[1])})'
                print(query)              
                hook.run(sql=query)
                
# A DAG represents a workflow, a collection of tasks
default_args = {    
    "start_date": datetime(2022,12,8)    
}
    
with DAG(dag_id="hard_dag", default_args=default_args, schedule_interval= "30-34 16 * * *", max_active_runs=5, catchup=False) as dag:    
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
    #читает текстовый файл и создает таблицу аналогичной структуры в Postgres и наполняет ее данными из файла(за иск. последнего числа)    
    file_exist = PythonOperator(task_id='file_exist', python_callable = make_table)
    #печатает сообщение об ошибке - файл не существует или в нем нет данных
    error_task = PythonOperator(task_id="error_task", python_callable = file_error)
    select_next_task = BranchPythonOperator(task_id='select_next_task',
                                        python_callable=select_next_task,
                                        dag=dag)
    #заполняем значениями колонку coef 
    change_table_task = PostgresOperator(
        task_id="chahge_table",
        postgres_conn_id=Variable.get("conn_id"),
        sql="ALTER TABLE IF EXISTS rnd_table ADD COLUMN IF NOT EXISTS coef integer;\
            update rnd_table\
            set coef = calc_coef.total\
            from (select s.*,\
                  coalesce(sum(s.value_1-s.value_2) over (order by s.id \
                  rows between unbounded preceding and current row),\
                  0) as total\
                  from rnd_table s\
            order by s.id) calc_coef\
            where rnd_table.id= calc_coef.id"
    )
    postgres_conn_id="postgres_default",
    bash_task >> python_task >> TwoNumsPrt_task >> TwoNumsCalc_task >> sens >>select_next_task>> [file_exist,error_task]
    file_exist>>change_table_task