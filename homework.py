import logging
import os
import telegram
import requests
import time
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if all([PRACTICUM_TOKEN is not None,
            TELEGRAM_TOKEN is not None,
            TELEGRAM_CHAT_ID is not None]):
        return True
    else:
        logging.critical('Отсутствует обязательная переменная окружения.')
        raise KeyError('Отсутствует обязательная переменная окружения.')
        exit()


def send_message(bot, message):
    """Отправляет сообщение в Телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Бот отправил сообщение: {message}')
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
    except Exception as error:
        logging.error(error)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f'Код ответа API: {response.status_code}')
        raise KeyError(f'Код ответа API: {response.status_code}')


def check_response(response):
    """Проверяет ответ API ."""
    if isinstance(response, dict):
        if isinstance(response.get('homeworks'), list):
            if response.get('homeworks') != []:
                return response.get('homeworks')[0]
            else:
                return []
        else:
            logging.error('Не соответствует типу')
            raise TypeError('Не соответсвует типу')
    else:
        logging.error('Не соответсвует типу')
        raise TypeError('Не соответсвует типу')


def parse_status(homework):
    """Извлекает статус работы."""
    if homework == []:
        return 'Статус не изменился'
    if homework.get('homework_name') is not None:
        homework_name = homework.get('homework_name')
    else:
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
    if homework.get('status') is not None:
        status = homework.get('status')
    else:
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error('Неожиданный статус домашней работы')
        raise KeyError('Неожиданный статус домашней работы')


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    check_tokens()
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message != 'Статус не изменился':
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
