# Фитнес-бот для Telegram

Бот с программами тренировок и отслеживанием прогресса (вес, замеры, достижения).

## Установка

1. Клонируй или скопируй проект, перейди в папку проекта.

2. Создай виртуальное окружение и установи зависимости:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Создай бота в Telegram:
   - Открой [@BotFather](https://t.me/BotFather).
   - Отправь `/newbot`, укажи имя и username бота.
   - Скопируй выданный токен.

4. Создай файл `.env` в корне проекта (по образцу `.env.example`):

   ```
   BOT_TOKEN=твой_токен_от_BotFather
   ```

5. Запуск:

   ```bash
   python -m bot.main
   ```

   Или из корня: `python -m bot.main` (запуск из папки с `bot`).

## Иллюстрации

- В коде используются пути:
  - `assets/images/workouts/{image_slug}.png` — картинки программ.
  - `assets/images/exercises/{image_slug}.png` — картинки упражнений.
- Если файла по `image_slug` нет, подставляется `assets/images/placeholder.png` (если файл есть).
- Чтобы везде показывались картинки до добавления своих:
  - Положи любую картинку в `assets/images/placeholder.png`.
- Свои иллюстрации: добавь файлы с именами из полей `image_slug` в `bot/data/programs.json` в папки `assets/images/workouts/` и `assets/images/exercises/` (форматы: .png, .jpg, .jpeg, .webp).

## Структура

- `bot/main.py` — запуск бота и роутеров.
- `bot/handlers/` — команды и сценарии (старт, тренировки, прогресс).
- `bot/keyboards/` — кнопки меню и inline-клавиатуры.
- `bot/storage/` — работа с SQLite (пользователи, прогресс).
- `bot/data/programs.json` — программы и упражнения (можно править и добавлять свои).
- `data/fitness.db` — база SQLite (создаётся при первом запуске).

## Функции

- **Тренировки:** выбор программы → список упражнений → карточка упражнения (описание + фото).
- **Прогресс:** добавление веса, замеров (название + значение + единица), достижений; просмотр истории.
