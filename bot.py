import logging
import os
import time
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import json
import threading

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Токен бота из переменных окружения Render
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Файл для хранения статистики
STATS_FILE = "bot_stats.json"

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                if "📚 История" in stats:
                    stats["📚 История кафедры"] = stats["📚 История"]
                    del stats["📚 История"]
                return stats
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
    
    return {
        "📢 Новости": 0,
        "🗓️ Расписание консультаций": 0,
        "📚 История кафедры": 0,
        "🎓 Абитуриентам": 0,
        "👨‍🎓 Студентам": 0,
        "⚽ Спортивная работа": 0,
        "🏅 Центр тестирования ГТО": 0,
        "👨‍🏫 Сотрудники кафедры": 0
    }

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

button_stats = load_stats()

# Тексты для разных разделов
WELCOME_TEXT = """
<b>Вы находитесь на официальном канале кафедры теории и методики массовой физкультурно-оздоровительной работы НГУ им. П.Ф. Лесгафта, Санкт-Петербург</b>
"""

NEWS_TEXT = """
<b>📢 Новости кафедры</b>

Здесь будут размещаться актуальные новости и события кафедры теории и методики массовой физкультурно-оздоровительной работы.

Следите за обновлениями!
"""

CONSULTATION_SCHEDULE_TEXT = """
<b>🗓️ Расписание консультаций</b>

Расписание консультаций преподавателей кафедры:

<u>Понедельник:</u> 10:00 - 12:00
<u>Вторник:</u> 14:00 - 16:00  
<u>Среда:</u> 10:00 - 12:00
<u>Четверг:</u> 14:00 - 16:00
<u>Пятница:</u> 10:00 - 12:00

Для уточнения расписания конкретного преподавателя обращайтесь по телефону кафедры.
"""

HISTORY_TEXT = """
<b>📚 История кафедры</b>

Кафедра теории и методики массовой физкультурно-оздоровительной работы была создана в 1983 году как кафедра массовой физкультурно-оздоровительной работы и туризма.

За время существования кафедрой руководили:
• 1983-1996: к.п.н., доцент В.Г. Каневец
• 1996-2000: к.п.н., доцент Т.В. Казанкина
• 2001-2011: академик РАТ Ю.Н. Федотов
• 2011-2015: Ю.В. Шулико
• 2015-2025: к.п.н., доцент А.Б. Петров
• С 2025: к.п.н., доцент Ю.Ю. Вишнякова

Кафедра готовит специалистов по направлениям:
• Физкультурно-оздоровительные технологии
• Спортивно-оздоровительный туризм
• Кёрлинг
"""

APPLICANTS_TEXT = """
<b>🎓 Абитуриентам</b>

<u>Направления подготовки:</u>
• Бакалавриат: 49.03.01 Физическая культура. Направленность (профиль) «Физкультурно-оздоровительная деятельность»
• Бакалавриат: 49.03.04 Спорт. Направленность (профиль) «Тренерско-преподавательская деятельность в избранном виде спорта» (полиатлон)
• Магистратура: 49.04.03 Спорт

Уважаемые абитуриенты! Вся актуальная информация на странице приемной комиссии НГУ им. П.Ф.Лесгафта, Санкт-Петербург
https://lesgaft.spb.ru/ru/commission/priyomnaya-komissiya
"""

STUDENTS_TEXT = """
<b>👨‍🎓 Студентам</b>

<u>Учебные материалы:</u>
Доступ к учебным материалам и расписанию занятий предоставляется через внутренний портал университета.

<u>Зачеты и экзамены:</u>
Расписание сессии публикуется на кафедре и сайте университета.

<u>Курсовые и дипломные работы:</u>
Темы курсовых и дипломных работ согласовываются с научными руководителями.
"""

SPORTS_WORK_TEXT = """
<b>⚽ Спортивная работа</b>

Кафедра активно участвует в спортивной жизни университета:

• Организация спортивных мероприятий
• Подготовка сборных команд
• Проведение соревнований
• Развитие студенческого спорта

Студенты кафедры регулярно участвуют в различных спортивных соревнованиях городского и всероссийского уровня.
"""

GTO_TESTING_CENTER_TEXT = """
<b>🏅 Центр тестирования ГТО</b>

<b>ПОДГОТОВКА К СДАЧЕ НОРМАТИВОВ ВФСК ГТО</b>

<u>📅 Сроки:</u> 
Первый квартал 2026 года (январь – март)

<u>🕒 График занятий:</u> 
2 раза в неделю (понедельник, среда) с 17.00

<u>💰 Стоимость обучения:</u> 
21 500 рублей

<u>📍 Место проведения:</u> 
Санкт-Петербург, ул. Декабристов, 35.

<u>📞 Контакты:</u>
Аксенова Наталья Николаевна
📧 n.aksenova@lesgaft.spb.ru 
📱 +7 904 618-33-11
"""

STAFF_TEXT = """
<b>👨‍🏫 Сотрудники кафедры</b>

<u>Заведующий кафедрой:</u>
<b>Вишнякова Юлия Юрьевна</b> - к.п.н., доцент, зав. каф.

<u>Профессорско-преподавательский состав:</u>
• <b>Лаврухина Галина Михайловна</b> - к.п.н., доцент
• <b>Горбунова Татьяна Владимировна</b> - старший преподаватель
• <b>Аксенова Наталья Николаевна</b> - к.п.н., доцент
• <b>Черная Анастасия Игоревна</b> - к.п.н., доцент
• <b>Фигон Яана Юрьевна</b> - преподаватель
• <b>Соколов Максим Сергеевич</b> - преподаватель
• <b>Степин Илья Евгеньевич</b> - преподаватель
• <b>Константинова Анастасия Константиновна</b> - старший преподаватель
• <b>Фоль Анастасия Сергеевна</b> - преподаватель
"""

def get_main_keyboard():
    keyboard = [
        ["📢 Новости", "🗓️ Расписание консультаций"],
        ["📚 История кафедры", "🎓 Абитуриентам"],
        ["👨‍🎓 Студентам", "⚽ Спортивная работа"],
        ["🏅 Центр тестирования ГТО", "👨‍🏫 Сотрудники кафедры"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(WELCOME_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text = update.message.text
        
        if text == "📢 Новости":
            button_stats["📢 Новости"] += 1
            await update.message.reply_text(NEWS_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "🗓️ Расписание консультаций":
            button_stats["🗓️ Расписание консультаций"] += 1
            await update.message.reply_text(CONSULTATION_SCHEDULE_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "📚 История кафедры":
            button_stats["📚 История кафедры"] += 1
            await update.message.reply_text(HISTORY_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "🎓 Абитуриентам":
            button_stats["🎓 Абитуриентам"] += 1
            await update.message.reply_text(APPLICANTS_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "👨‍🎓 Студентам":
            button_stats["👨‍🎓 Студентам"] += 1
            await update.message.reply_text(STUDENTS_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "⚽ Спортивная работа":
            button_stats["⚽ Спортивная работа"] += 1
            await update.message.reply_text(SPORTS_WORK_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "🏅 Центр тестирования ГТО":
            button_stats["🏅 Центр тестирования ГТО"] += 1
            await update.message.reply_text(GTO_TESTING_CENTER_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        elif text == "👨‍🏫 Сотрудники кафедры":
            button_stats["👨‍🏫 Сотрудники кафедры"] += 1
            await update.message.reply_text(STAFF_TEXT, parse_mode='HTML', reply_markup=get_main_keyboard())
            
        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню для навигации.", reply_markup=get_main_keyboard())
        
        save_stats(button_stats)
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        stat_text = "<b>📊 Статистика обращений:</b>\n\n"
        for button, count in button_stats.items():
            stat_text += f"• {button}: {count}\n"
        stat_text += f"\nВсего: {sum(button_stats.values())}"
        await update.message.reply_text(stat_text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка в команде stat: {e}")

async def statreset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        for button in button_stats:
            button_stats[button] = 0
        save_stats(button_stats)
        await update.message.reply_text("✅ Статистика сброшена!")
    except Exception as e:
        logger.error(f"Ошибка в команде statreset: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Ошибка при обработке обновления: {context.error}")

def run_bot():
    """Запуск бота в отдельном потоке"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return
    
    try:
        # Создаем application с более старым методом для совместимости
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stat", stat_command))
        application.add_handler(CommandHandler("statreset", statreset_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)
        
        logger.info("🤖 Бот запускается...")
        
        # Простой запуск polling без дополнительных параметров
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def create_app():
    """Создание Flask приложения"""
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        total_requests = sum(button_stats.values())
        uptime_seconds = time.time() - start_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🤖 Бот кафедры ТиМ МФОР</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }}
                .status {{ 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin: 20px 0; 
                    text-align: center;
                }}
                .running {{ 
                    background: rgba(76, 175, 80, 0.2); 
                    border: 2px solid #4CAF50;
                }}
                a {{ 
                    color: #ffeb3b; 
                    text-decoration: none; 
                    font-weight: bold;
                }}
                a:hover {{ 
                    text-decoration: underline; 
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-item {{
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Telegram Bot</h1>
                <h2>Кафедра теории и методики массовой физкультурно-оздоровительной работы</h2>
                <p>НГУ им. П.Ф. Лесгафта, Санкт-Петербург</p>
                
                <div class="status running">
                    <strong>Статус:</strong> ✅ Активен и работает
                </div>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <h3>📊 Всего запросов</h3>
                        <p>{total_requests}</p>
                    </div>
                    <div class="stat-item">
                        <h3>🕒 Время работы</h3>
                        <p>{uptime_str}</p>
                    </div>
                </div>
                
                <h2>📋 Меню бота</h2>
                <ul>
                    <li>📢 Новости кафедры</li>
                    <li>🗓️ Расписание консультаций</li>
                    <li>📚 История кафедры</li>
                    <li>🎓 Абитуриентам</li>
                    <li>👨‍🎓 Студентам</li>
                    <li>⚽ Спортивная работа</li>
                    <li>🏅 Центр тестирования ГТО</li>
                    <li>👨‍🏫 Сотрудники кафедры</li>
                </ul>
                
                <h2>🔗 Ссылки</h2>
                <ul>
                    <li><a href="/health">Проверить статус сервиса</a></li>
                    <li><a href="/stats">Посмотреть статистику бота</a></li>
                    <li><a href="https://lesgaft.spb.ru">Сайт университета</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
    
    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "service": "telegram-bot",
            "timestamp": time.time(),
            "environment": "production"
        }, 200
    
    @app.route('/stats')
    def stats():
        return {
            "status": "running",
            "button_stats": button_stats,
            "total_requests": sum(button_stats.values()),
            "uptime_seconds": time.time() - start_time
        }
    
    return app

def run_flask():
    """Запуск Flask приложения"""
    app = create_app()
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Flask сервер запускается на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Глобальные переменные
start_time = time.time()

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 Запуск приложения...")
    print("📍 Кафедра ТиМ МФОР НГУ им. П.Ф. Лесгафта")
    print("🌐 Хостинг: Render.com")
    print("📚 Версия: python-telegram-bot 20.8")
    print("=" * 60)
    
    # Проверяем наличие токена
    if not BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не установлен!")
        print("Пожалуйста, установите переменную окружения BOT_TOKEN в настройках Render")
        return
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Telegram бот запущен в фоновом режиме")
    
    print("📊 Доступные endpoints:")
    print("   /          - Главная страница")
    print("   /health    - Health check")
    print("   /stats     - Статистика бота")
    print("=" * 60)
    print("⚡ Приложение готово к работе!")
    print("=" * 60)
    
    # Запускаем Flask (блокирующий вызов)
    run_flask()

if __name__ == "__main__":
    main()