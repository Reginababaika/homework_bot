# Проект "Телеграм бот-ассистент"

## Описание:

Телеграм бот-ассистент оценки статуса домашнего задания через API ' https://practicum.yandex.ru/api/user_api/homework_statuses/ ' и отправляет сообщение:

- Работа проверена: ревьюеру всё понравилось. Ура!
- Работа взята на проверку ревьюером.
- Работа проверена: у ревьюера есть замечания.

## Запуск проекта:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Reginababaika/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```
