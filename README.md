Практика. Airflow.
1. Запустите установку сборки образа Airflow: docker-compose up
2. После успешной установки вам будет доступе Airflow UI по адресу: http://localhost:8080. 
Для авторизации используйте сочетание airflow-airflow

Описание файла dags\light_dag.py:
создается DAG "light_dag" запускающийся 5 раз с интервалом 1 минута ежедневно в 20:19 UTC в нем 4 задачи:
	- bash_task - пример BashOperator, выводит hello;
	- python_task - пример PythonOperator, выводит world;
	- TwoNumsPrt_task	- генерирует 2 числа и записывает в текстовый файл light.txt через пробел,
		каждые два числа записываются с новой строки не затирая предыдущие;
	- TwoNumsCalc -подключается к файлу и вычисляет сумму всех чисел из первой колонки,
		затем сумму всех чисел из второй колонки и рассчитывает разность полученных сумм.
Вычисленную разность записывает в конец того же файла, не затирая его содержимого.

Описание файла dags\hard_dag.py:
-дополнительно в airflow:
	создать переменные (Admin\Variables)
		key=filename, val=/opt/airflow/hard.txt
		key=conn_id, val=postgre_con
	создать соединение (Admin\Connections)
		Conn_Id=postgre_con, Conn_Type=postgres, Host=host.docker.internal, Port=5430
		
создается DAG "hard_dag" запускающийся 5 раз с интервалом 1 минута ежедневно в 20:19 UTC в нем задачи:	
	- bash_task, python_task, TwoNumsPrt_task, TwoNumsCalc - аналогичны таковым в "light_dag"
	- sens - Sensor-оператор {should_continue}, который возвращает True в том случае, если выполнены следующие условия:
		i.     Файл существует {os.path.exists(filename)}
		#ii.     Количество строк в файле минус одна последняя - соответствует кол-ву запусков 
			{def check_file_count(afilename)  - пока в проекте, всегда возвращает True}
		iii.     Финальное число рассчитано верно.
			{def check_file_sum(afilename)}
	-select_next_task оператор ветвления, который в случае, если текстовый файл существует не пустой - создает таблицу
		аналогичной структуры в Postgres и наполняет ее данными из файла(за иск. последнего числа).
		В случае если файл не существует или в нем нет данных – печатает сообщение об ошибке
	-change_table_task Если удалось создать таблицу с данными –Postgres-оператор, который добавляет в таблицу еще одну колонку, 
		в которой будут размещаться числа рассчитанные по логике из пункта TwoNumsCalc

