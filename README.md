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

- **Backend:** Python 3.12, Django 5, Django REST Framework, PostgreSQL, Gunicorn;
- **Frontend:** HTML, CSS, JavaScript (React);
- **Контейнеризация:** Docker, Docker Compose;
- **CI/CD:** GitHub Actions;
- **Деплой:** Nginx (в качестве шлюза/прокси).

## Как развернуть проект

1. Клонируйте репозиторий на локальный компьютер;
2. Создайте файл .env в корне проекта и заполните его (см. раздел ниже);
3. Запустите контейнеры с помощью команды <docker compose -f docker-compose.production.yml up -d>;
4. Откройте проект в браузере по адресу http://localhost:7000, админку - http://localhost:7000/admin, документацию API (Redoc) - http://localhost:7000/redoc.

## Как заполнить файл .env

1. В корне проекта создайте файл .env;
2. Укажите в файле переменные из файла .env.example;
3. В .env присвойте переменным свои актуальные значения.

## Адрес проекта

https://foodgramartrus.servehttp.com/

## Автор

russinArtem