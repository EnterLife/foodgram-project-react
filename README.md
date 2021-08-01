# foodgram-project
![foodgram_workflow](https://github.com/EnterLife/foodgram-project/.github/workflows/foodgram_workflow.yml/badge.svg)

Дипломный проект — сайт Foodgram - «Продуктовый помощник».

Проект: http://enterlife.us

Документация API: http://enterlife.us/redoc/

Панель администратора: http://enterlife.us/admin/

# Порядок установки
## В режиме разработки
1. Установить виртуальный интерпретатор `python3 -m venv venv`

После выполнения этой команды в директории проекта появится папка venv, в которой хранятся служебные файлы виртуального окружения. Там же будут сохранены все зависимости проекта.

2. Ативировать виртуальное окружение в зависимости от операционной системы  
   Unix-системы: `source venv/bin/activate`  
   Windows: `source venv/Scripts/activate`

В терминале появится уведомление о том, что вы работаете в виртуальном окружении: строка  (venv) будет предварять все команды.

3. Установите необходимые пакеты `pip install -r requirements.txt`
4. Запустите приложение в терминале `python manage.py runserver`
## В режиме запуска на сервере
1. Переименуйте файл .evn.example в .env, внесите ваши настройки согласно примеру  
2. Запустите докер  
   ```docker-compose up -d --build```  
3. Создайте необходимые миграции:   
   ```docker-compose exec web python manage.py makemigrations api```
4. Накатите созданные миграции в БД  
```docker-compose exec web python manage.py migrate```
5. Создайте суперпользователя:  
```docker-compose exec web python manage.py createsuperuser```
6. Соберите статику  
```docker-compose exec web python manage.py collectstatic --no-input```
7. Приложение будет доступно по адресу  
```http://127.0.0.1/```
   
# Загрузка тестовых данных  
1. Запустите приложение
   ```docker-compose up -d --build```
2. Откройте терминал сервиса web
   ```docker-compose exec web bash```
3. Выполните последовательно следующий код:
```python3 manage.py shell```
```python
from django.contrib.contenttypes.models import ContentType
ContentType.objects.all().delete()
quit()
```
```python manage.py loaddata fixtures.json```
