import logging
import os
import threading
import time
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

# Отключаем логирование для httpx и httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Токен бота из переменных окружения Render
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Файл для хранения статистики
STATS_FILE = "bot_stats.json"

# Глобальные переменные
button_stats = {}
bot_application = None

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
        "📢 Новости": 0, "🗓️ Расписание консультаций": 0, "📚 История кафедры": 0,
        "🎓 Абитуриентам": 0, "👨‍🎓 Студентам": 0, "⚽ Спортивная работа": 0,
        "🏅 Центр тестирования ГТО": 0, "👨‍🏫 Сотрудники кафедры": 0
    }

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

# Инициализация статистики
button_stats = load_stats()

# Тексты для разных разделов (сокращенные версии для примера)
WELCOME_TEXT = "Вы находитесь на официальном канале кафедры теории и методики массовой физкультурно-оздоровительной работы НГУ им. П.Ф. Лесгафта, Санкт-Петербург"

NEWS_TEXT = "📢 Новости кафедры - здесь будут размещаться актуальные новости и события кафедры."

CONSULTATION_SCHEDULE_TEXT = """
🗓️ Расписание консультаций

Понедельник: 10:00 - 12:00
Вторник: 14:00 - 16:00  
Среда: 10:00 - 12:00
Четверг: 14:00 - 16:00
Пятница: 10:00 - 12:00
"""

# Остальные тексты (вставьте ваши полные тексты)
HISTORY_TEXT_PART1 = "📚 История кафедры - часть 1..."
HISTORY_TEXT_PART2 = "📚 История кафедры - часть 2..."
HISTORY_TEXT_PART3 = "📚 История кафедры - часть 3..."
HISTORY_TEXT_PART4 = "📚 История кафедры - часть 4..."
HISTORY_TEXT_PART5 = "📚 История кафедры - часть 5..."
APPLICANTS_TEXT = "🎓 Абитуриентам - информация для поступающих..."
STUDENTS_TEXT = "👨‍🎓 Студентам - учебные материалы и расписание..."
SPORTS_WORK_TEXT = "⚽ Спортивная работа - мероприятия и соревнования..."
GTO_TESTING_CENTER_TEXT = "🏅 Центр тестирования ГТО - подготовка к сдаче нормативов..."
GTO_TESTING_CENTER_TEXT_PART2 = "🏅 Центр тестирования ГТО - контакты и преимущества..."
STAFF_TEXT = "👨‍🏫 Сотрудники кафедры - список преподавателей..."

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
            history_parts = [HISTORY_TEXT_PART1, HISTORY_TEXT_PART2, HISTORY_TEXT_PART3, HISTORY_TEXT_PART4, HISTORY_TEXT_PART5]
            for part in history_parts:
                await update.message.reply_text(part, parse_mode='HTML')
            await update.message.reply_text("История кафедры завершена.", reply_markup=get_main_keyboard())
            
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
            await update.message.reply_text(GTO_TESTING_CENTER_TEXT, parse_mode='HTML')
            await update.message.reply_text(GTO_TESTING_CENTER_TEXT_PART2, parse_mode='HTML', reply_markup=get_main_keyboard())
            
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
    """Запускает Telegram бота в отдельном потоке"""
    global bot_application
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return
    
    try:
        bot_application = Application.builder().token(BOT_TOKEN).build()
        
        bot_application.add_handler(CommandHandler("start", start))
        bot_application.add_handler(CommandHandler("stat", stat_command))
        bot_application.add_handler(CommandHandler("statreset", statreset_command))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_application.add_error_handler(error_handler)
        
        print("🤖 Запуск Telegram бота...")
        bot_application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def create_flask_app():
    """Создает и настраивает Flask приложение"""
    app = Flask(__name__)

    @app.route('/')
    def home():
        return """
        <h1>🤖 Telegram Bot для кафедры ТиМ МФОР</h1>
        <p>Бот успешно работает на Render!</p>
        <p><a href="/health">Проверить статус</a></p>
        <p><a href="/stats">Посмотреть статистику</a></p>
        """

    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "service": "telegram-bot",
            "timestamp": time.time(),
            "bot_running": bot_application is not None
        }, 200

    @app.route('/stats')
    def stats():
        return {
            "status": "running",
            "button_stats": button_stats,
            "total_requests": sum(button_stats.values()),
            "timestamp": time.time()
        }

    return app

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 Запуск приложения...")
    print("📍 Кафедра ТиМ МФОР НГУ им. П.Ф. Лесгафта")
    print("🌐 Хостинг: Render.com")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Telegram бот запущен в фоновом режиме")
    
    # Запускаем Flask в основном потоке
    app = create_flask_app()
    port = int(os.environ.get('PORT', 10000))
    
    print(f"🌐 Flask сервер запускается на порту {port}")
    print("📊 Endpoints:")
    print("   /       - Главная страница")
    print("   /health - Health check")
    print("   /stats  - Статистика бота")
    print("=" * 60)
    
    # Запускаем Flask (блокирующий вызов)
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()