# foodgram-project
![foodgram_workflow](https://github.com/EnterLife/foodgram-project-react/actions/workflows/main.yml/badge.svg)

Дипломный проект — сайт Foodgram - «Продуктовый помощник».

Проект: 
http://178.154.192.209/recipes

http://178.154.192.209/admin admin@mail.com admin

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
1. Запустите докер   
```docker-compose up -d --build```   
2. Создайте необходимые миграции:    
```docker-compose exec backend python manage.py makemigrations api``` 
3. Накатите созданные миграции в БД   
```docker-compose exec backend python manage.py migrate``` 
4. Создайте суперпользователя:   
```docker-compose exec backend python manage.py createsuperuser``` 
5. Соберите статику   
```docker-compose exec backend python manage.py collectstatic --no-input``` 
6. Приложение будет доступно по адресу   
```http://127.0.0.1/``` 
    
# Загрузка тестовых данных   
1. Запустите приложение 
   ```docker-compose up -d --build``` 
2. Откройте терминал сервиса web 
   ```docker-compose exec backend bash``` 
3. Выполните последовательно следующий код: 
```python3 manage.py shell``` 
```python 
from django.contrib.contenttypes.models import ContentType 
ContentType.objects.all().delete() 
quit() 
``` 
```python manage.py loaddata fixtures.json```