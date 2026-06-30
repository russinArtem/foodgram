# Foodgram — продуктовый помощник

[![Build Status](https://github.com/russinArtem/kittygram_final/actions/workflows/main.yml/badge.svg)](https://github.com/russinArtem/kittygram_final/actions/workflows/main.yml)
[![Python version](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/downloads/release/python-312/)

## Описание проекта

**Foodgram** — это сервис для публикации и обмена рецептами. Пользователи могут:
- регистрироваться и авторизовываться в системе;
- публиковать свои рецепты с пошаговым описанием и фотографиями;
- добавлять чужие рецепты в избранное;
- подписываться на публикации других авторов;
- формировать список покупок из выбранных рецептов и скачивать его.

## Стек технологий

- **Backend:** Python 3.12, Django 5, Django REST Framework, Gunicorn;
- **База данных:** PostgreSQL;
- **Аутентификация:** Djoser (DRF Token Authentication);
- **Фронтенд:** HTML, CSS, JavaScript (React);
- **Контейнеризация:** Docker, Docker Compose;
- **CI/CD:** GitHub Actions;
- **Веб-сервер:** Nginx;
- **Документация API:** ReDoc (OpenAPI);
- **Фильтрация и поиск:** Django Filter;
- **Обработка изображений:** drf-extra-fields.

---

## Локальное развертывание проекта (без Docker)

Для разработки и тестирования можно запустить проект локально, без Docker.

### 1. Клонируйте репозиторий и перейдите в него в командной строке

```
git clone https://github.com/russinArtem/foodgram.git
cd foodgram
```

**Примечаие:** репозиторий приватный, запросите доступ у автора.

### 2. Создайте и активируйте виртуальное окружение

```
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас Windows

    ```
    source venv/Scripts/activate
    ```

### 3. Обновите пакетный менеджер `pip` и установите зависимости из файла `requirements.txt`

```
python3 -m pip install --upgrade pip
```

```
pip install -r backend/requirements.txt
```

### 4. Создайте и заполните файл `.env`, при необходимости настройте PostgreSQL

В корне проекта создайте файл `.env` и укажите в нем переменные из файла `.env.example` в зависимости оттого, какую БД планируете использовать. В `.env` присвойте переменным свои актуальные значения.

### 5. Выполните миграции, создайте суперпользователя и импортируйте данные

```
cd backend
python3 manage.py migrate
```

```
python3 manage.py createsuperuser
```

```
python3 manage.py import_ingredients
python3 manage.py import_tags
```

### 6. Запустите сервер разработки

```
python3 manage.py runserver
```

Проект будет доступен по адресам:
- [Сайт](http://localhost:8000/)
- [Админ-панель](http://localhost:8000/admin/)
- [Документация API (ReDoc)](http://localhost:8000/redoc/)

---

## Развертывание проекта через Docker

### 1. Клонируйте репозиторий и перейдите в него в командной строке

```
git clone https://github.com/russinArtem/foodgram.git
cd foodgram
```

**Примечаие:** репозиторий приватный, запросите доступ у автора.

### 2. Создайте и заполните файл `.env`

В корне проекта создайте файл `.env` и укажите в нем переменные из файла `.env.example`. В `.env` присвойте переменным свои актуальные значения.

### 3. Запустите и проверьте контейнеры

```
docker compose -f docker-compose.production.yml up -d
```

```
docker compose -f docker-compose.production.yml ps
```

### 4. Соберите и скопируйте статику, примените миграции, создайте суперпользователя и импортируйте данные

```
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```

```
docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

```
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

```
docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

```
docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
docker compose -f docker-compose.production.yml exec backend python manage.py import_tags
```

Проект будет доступен по адресам:
- [Сайт](http://localhost:7000/)
- [Админ-панель](http://localhost:7000/admin/)
- [Документация API (ReDoc)](http://localhost:7000/api/docs/)

---

## Проект

| Ресурс | Ссылка |
|--------|--------|
| Сайт | [https://foodgramartrus.servehttp.com/](https://foodgramartrus.servehttp.com/) |
| Админ-панель | [https://foodgramartrus.servehttp.com/admin/](https://foodgramartrus.servehttp.com/admin/) |
| Документация API (ReDoc) | [https://foodgramartrus.servehttp.com/api/docs/](https://foodgramartrus.servehttp.com/api/docs/) |

---

## Автор

**Артем Руссин**

GitHub: [russinArtem](https://github.com/russinArtem/)

Email: [russinartem@yandex.ru](mailto:russinartem@yandex.ru)

## Лицензия

Проект выполнен в рамках учебного курса [Яндекс.Практикум](https://practicum.yandex.ru/).