import logging
import os
import telegram
import requests
import time
import sys
from dotenv import load_dotenv
from exceptions import EmptyAPIResponseError, WrongAPIResponseCodeError
from exceptions import TelegramError
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
Dict = {}
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN,
                TELEGRAM_TOKEN,
                TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Телеграм."""
    try:
        logging.debug(f'Cообщение: {message}')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=str(message))
    except telegram.error.TelegramError as error:
        logging.error(error)
        raise TelegramError(f'Ошибка отправки телеграм сообщения: {error}')
    else:
        logging.debug(f'Бот отправил сообщение: {message}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        timestamp = int(time.time())
        request_params = {
            'url': ENDPOINT,
            'headers': HEADERS,
            'params': {'from_date': timestamp}
        }
        logging.info(
            (
                'Начинаем подключение к эндпоинту {url}, с параметрами'
                ' headers = {headers} ;params= {params}.'
            ).format(**request_params)
        )
        response = requests.get(**request_params)
    except Exception as error:
        logging.error(error)
        raise ConnectionError(
            (
                'Во время подключения к эндпоинту {url} произошла'
                ' непредвиденная ошибка: {error}'
                ' headers = {headers}; params = {params};'
            ).format(
                error=error,
                **request_params
            )
        )
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f'Код ответа API: {response.status_code}')
        raise WrongAPIResponseCodeError(
            'Ответ сервера не является успешным:'
            f' request params = {request_params};'
            f' http_code = {response.status_code};'
            f' reason = {response.reason}; content = {response.text}'
        )


def check_response(response):
    """Проверяет ответ API."""
    logging.info('Начинаем проверку ответа API')
    if isinstance(response, dict):
        if isinstance(response.get('homeworks'), list):
            if 'homeworks' in response.keys(
            ) and 'current_date' in response.keys():
                return response.get('homeworks')
            else:
                raise EmptyAPIResponseError(
                      'В ответе API отсутствуют необходимые'
                      'ключи "homeworks" и/или'
                      f' "current_date", response = {response}.'
                      )
                logging.error('Отсутствие ожидаемых ключей в ответе API')
        else:
            logging.error('Не соответствует типу')
            raise TypeError('Не соответсвует типу')
    else:
        logging.error('Не соответсвует типу')
        raise TypeError('Не соответсвует типу')


def parse_status(homework):
    """Извлекает статус работы."""
    if all([homework.get('homework_name'),
            homework.get('status')]):
        homework_name = homework.get('homework_name')
        status = homework.get('status')
    else:
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
        logging.error('Отсутствие ожидаемых ключей в ответе API')
    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error('Неожиданный статус домашней работы')
        raise KeyError('Неожиданный статус домашней работы')


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    check_tokens()
    if not check_tokens():
        message = (
            'Отсутсвуют обязательные переменные окружения: PRACTICUM_TOKEN,'
            ' TELEGRAM_TOKEN, TELEGRAM_CHAT_ID.'
            ' Программа принудительно остановлена.'
        )
        logging.critical(message)
        sys.exit(message)
    while True:
        current_report: Dict = {'name': '', 'output': ''}
        prev_report: Dict = current_report.copy()
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            new_homeworks = check_response(response)
            if new_homeworks:
                current_report['name'] = new_homeworks[0]['homework_name']
                current_report['output'] = parse_status(new_homeworks[0])
            else:
                current_report['output'] = (
                    f'За период от {current_timestamp} до настоящего момента'
                    ' домашних работ нет.'
                )
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()
            else:
                logging.debug('В ответе нет новых статусов.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['output'] = message
            logging.error(message, exc_info=True)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
