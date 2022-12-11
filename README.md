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
создается DAG "hard_dag" запускающийся 5 раз с интервалом 1 минута ежедневно в 20:19 UTC в нем задачи:	
	- bash_task, python_task, TwoNumsPrt_task, TwoNumsCalc - аналогичны таковым в "light_dag"
	- sens - Sensor-оператор {should_continue}, который возвращает True в том случае, если выполнены следующие условия:
		i.     Файл существует {os.path.exists(filename)}
		#ii.     Количество строк в файле минус одна последняя - соответствует кол-ву запусков 
			{def check_file_count(afilename)  - пока в проекте, всегда возвращает True}
		iii.     Финальное число рассчитано верно.
			{def check_file_sum(afilename)}


