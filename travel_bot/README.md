# Travel Bot — перелёты и отели в Telegram

Бот для личного использования: поиск перелётов (Google Flights) и отелей (Google Hotels) по лучшим ценам с AI-анализом комбо.

## Установка за 5 минут

```bash
cd travel_bot
pip install -r requirements.txt
cp .env.example .env
```

Откройте `.env` и заполните ключи API:

- **TELEGRAM_TOKEN** — токен бота от [@BotFather](https://t.me/BotFather)
- **SERPAPI_KEY** — ключ с [serpapi.com](https://serpapi.com) (Google Flights + Google Hotels). Бесплатный план: 250 поисков/месяц
- **OPENAI_API_KEY** — ключ OpenAI для анализа комбо (gpt-4o-mini)
- **DEFAULT_ORIGIN_AIRPORT** — IATA код аэропорта вылета по умолчанию (например `BRU` для Брюсселя)
- **CURRENCY** — валюта, например `EUR`
- **ALLOWED_TELEGRAM_IDS** — необязательно: через запятую ID пользователей Telegram; если пусто — бот доступен всем

Запуск:

```bash
python main.py
```

В Telegram: найдите бота и отправьте `/start`.

## Команды

| Команда    | Описание                    |
|-----------|-----------------------------|
| `/start`  | Приветствие и пример запроса |
| `/search` | Подсказка, как ввести запрос |
| `/history`| История сохранённых поисков  |
| `/settings` | Текущий аэропорт и валюта (читаются из .env) |
| `/help`   | Справка по командам          |

Можно сразу написать запрос текстом, например:

```
Барселона 15-22 июля, 2 человека, 4*, бюджет 1500€
```

## Источники данных

- **Перелёты:** SerpAPI → Google Flights  
- **Отели:** SerpAPI → Google Hotels (агрегатор, не только Booking.com)  
- **Анализ комбо и скидок:** OpenAI (gpt-4o-mini)

При отсутствии ключей или ошибке API бот возвращает заглушки, чтобы интерфейс и кнопки всегда можно было проверить.

## Структура проекта

```
travel_bot/
├── main.py           # Точка входа, обработчики команд и сообщений
├── search_flights.py # SerpAPI Google Flights + fallback
├── search_hotels.py  # SerpAPI Google Hotels + fallback
├── ai_analyzer.py    # OpenAI анализ комбо
├── database.py       # SQLite — история поисков
├── config.py         # Загрузка .env
├── keyboards.py      # Inline-кнопки
├── utils.py          # Парсинг запроса (даты, город, звёзды, бюджет)
├── .env.example
├── requirements.txt
└── README.md
```

## Ограничения

- Бот не бронирует билеты и отели, не принимает платежи
- Регистрация пользователей не требуется (опционально — ограничение по Telegram ID в .env)
- Город вылета по умолчанию — один (из .env); список городов для парсинга ограничен (см. `utils.CITY_TO_IATA`)
