import os
import telebot
from telebot import types
import logging
import time
from requests.exceptions import ReadTimeout, ConnectionError

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация бота с увеличенными таймаутами
bot = telebot.TeleBot("8028394564:AAFZD7WgRnXWE4zuWQ2n6HeoX7_iM5TBDr8")

# Папка для хранения данных
DATA_FOLDER = "taxi_database"

# ID админа (установлен вручную)
ADMIN_ID = 1941772742

# Словарь для хранения заявок на одобрение
pending_approvals = {}

# Создаем основную папку если ее нет
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Словарь для хранения временных данных пользователей
user_data = {}

# Языки
class Language:
    UZBEK = 'uz'
    RUSSIAN = 'ru'

# Состояния регистрации
class RegistrationState:
    START = 0
    LANGUAGE_SELECTION = 1
    LICENSE_FRONT = 2
    LICENSE_BACK = 3
    PASSPORT_FRONT = 4
    PASSPORT_BACK = 5
    PHONE = 6

def get_user_state(user_id):
    """Получает текущее состояние пользователя"""
    if user_id in user_data:
        return user_data[user_id].get('state', RegistrationState.START)
    return RegistrationState.START

def get_user_language(user_id):
    """Получает язык пользователя"""
    if user_id in user_data:
        return user_data[user_id].get('language', Language.UZBEK)
    return Language.UZBEK

# Тексты на разных языках
TEXTS = {
    Language.UZBEK: {
        'choose_language': "🇺🇿 🇷🇺 Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        'welcome': (
            "👋 Salom! Yengil Taksi botiga xush kelibsiz!\n\n"
            "🚖 Bu yerda siz uchun eng qulay, daromadli va ishonchli taksopark tariflari jamlangan.\n"
            "🏆 Bizda 3 ta yuqori darajadagi tarif mavjud — har biri o'zining afzalliklari, bonuslari "
            "va barqaror daromad imkoniyatlari bilan ajralib turadi.\n\n"
            "ℹ️ Qaysi tarif yoki ma'lumot bilan tanishmoqchisiz? Pastdan tanlang:"
        ),
        'main_menu': "🏠 **Asosiy menyu:**\n\nKerakli bo'limni tanlang va daromadingizni oshirishni boshlang!",
        'please_select': "Iltimos, menyudan kerakli bo'limni tanlang.",
        'about_taxipark': (
            "🏆Yengil TAXI - Bu Ishonch va Barqaror Daromad!\n\n"
            "✨ *Nega bizni tanlashadi?*\n\n"
            "✅ Shahardagi eng arzon Foizlar\n"
            "✅ 24/7 texnik va dispetcherlik qo'llab-quvvatlash\n"
            "✅ Taksopark Bonuslari\n"
            "✅ Qulay pul to'ldirish va yechish\n\n"
            "💰 *Daromadingizni oshiring:*\n"
            "• Kuniga 500,000 so'm daromad\n"
            "• Bonuslar va rag'batlantirish dasturlari\n"
            "• Ikkilamchi daromad manbalari\n\n"
            "🎯 *Bizning maqsad:*\n"
            "Haydovchilarimizni barqaror va yuqori daromadli hamkorlar qilish!"
        ),
        'percentages_menu': (
            "🚗 **Tariflar tanlang:**\n\n"
            "Har bir tarif maxsus imtiyozlar va afzalliklar bilan. "
            "O'zingizga mos Tarifni tanlang va daromadingizni oshiring!"
        ),
        'dispatcher_info': (
            "📞 **Dispecher bilan aloqa**\n\n"
            "Quyidagi shaharlarimiz bo'yicha dispecherlar bilan bog'lanishingiz mumkin.\n"
            "Kerakli shaharni tanlang va uning Telegram akkauntiga o'ting:"
        ),
        'kokand_dispatcher': (
            "🏙️ Qoqon Dispecherlari\n\n"
            "Kokand shahri bo'yicha bizning dispecherlarimiz:\n\n"
            "📱 Telefon: +998 90 509 00 90\n"
            "📧 Telegram: @yengiltaxi_reg\n\n"
            "🕐 Ish vaqti: 08:00 - 22:00\n"
            "📍 Manzil: Qoqon Алишера Навоий 12A\n\n"
            "✅ Xizmatlar: \n"
            "• Haydovchi ro'yxatdan o'tkazish\n"
            "• Texnik masalalar\n"
            "• To'lov va hisob-kitoblar\n"
            "• Muhim yangiliklar\n\n"
            "Bog'lanish uchun yuqoridagi Telegram akkauntlaridan biriga yozing!"
        ),
        'andijan_dispatcher': (
            "🏙️ Andijan Dispecherlari\n\n"
            "Andijan shahri bo'yicha bizning dispecherlarimiz:\n\n"
            "📱 Telefon: +998 33 508 00 90\n"
            "📧 Telegram: @yandexgo_andijon60\n\n"
            "🕐 Ish vaqti: 08:00 - 22:00 \n"
            "📍 Manzil: Babur prospekti, Andijon, 222 yo'li ✅\n\n"
            "✅ Xizmatlar: \n"
            "• Haydovchi ro'yxatdan o'tkazish\n"
            "• Texnik masalalar\n"
            "• To'lov va hisob-kitoblar\n"
            "• Muhim yangiliklar\n\n"
            "Bog'lanish uchun yuqoridagi Telegram akkauntlaridan biriga yozing!"
        ),
        'fergana_dispatcher': (
            "🏙️ Farg'ona Dispecherlari\n\n"
            "Farg'ona shahri bo'yicha bizning dispecherlarimiz:\n\n"
            "📱 Telefon: +998 33 509 00 90\n"
            "📧 Telegram: @yandexgo_fergana\n\n"
            "🕐 Ish vaqti: 08:00 - 22:00\n"
            "📍 Manzil: Farg'ona,\n\n"
            "✅ Xizmatlar: \n"
            "• Haydovchi qabul qilish\n"
            "• Aeroport transferlari\n"
            "• Korporativ mijozlar\n"
            "• Premium xizmatlar\n\n"
            "Bog'lanish uchun yuqoridagi Telegram akkauntlaridan biriga yozing!"
        ),
        'percent_1_info': (
            "🥉 *START TARIFI - 1%*\n"
            "_(Boshlang'ich daraja)_\n\n"
            "💰 *Daromad imkoniyatlari:*\n"
            "• *Kunlik daromad:* 200,000 - 400,000 so'm\n"
            "• *Komissiya:* Faqat **1%**\n\n"
            "💡 *Ideal kimlar uchun:* Yangi boshlovchilar\n\n"
            "🔥 *Boshlash uchun:* quyidagi tugmani bosing!"
        ),
        'percent_2_info': (
            "🥈 *PRO TARIFI - 2%*\n"
            "_(Professional daraja)_\n\n"
            
            "💰 *Daromad imkoniyatlari:*\n"
            "• *Oylik daromad:* 300,000 - 500,000 so'm\n"
            "• *Komissiya:* Faqat **2%** (optimal nisbat!)\n"
            "• *To'lov:* Har hafta yakshanba kuni\n"
            "• *Bonus:* **10% Keshbek**\n\n"
            
            "Tajribali haydovchilar va barqaror yuqori daromad "
            "qidirayotganlar uchun ajoyib tanlov!\n\n"
            
            "🔥 *Professional bo'lish uchun:* quyidagi tugmani bosing!"
        ),
        'percent_3_5_info': (
            "🥇 *VIP TARIFI - 3.5%*\n"
            "_(Elita daraja)_\n\n"
            
            "💰 *Elita daromadlari:*\n"
            "• *Kunlik daromad:* 400,000 - 600,000 so'm\n"
            "• *Komissiya:* Faqat **3.5%** (yuqori daromad uchun eng qulay!)\n"
            "• *Bonus:* Yandex tomonidan 1-2 haftalik maxsus bonuslar\n\n"
            
            "Elita haydovchilar, yuqori sifatli xizmat ko'rsatishni xohlaydiganlar "
            "va yuqori daromadga intiluvchilar uchun ajoyib tanlov!\n\n"
            
            "🔥 *Elita safiga qo'shilish:* quyidagi tugmani bosing!"
        ),
        'buttons': {
            'about': "Taksopark Haqida🧾",
            'percentages': "Taksopark Foizlari📊",
            'dispatcher': "Dispecher Bilan Aloqa📞",
            'kokand': "📍 Qoqon Dispecherlari",
            'andijan': "📍 Andijan Dispecherlari",
            'fergana': "📍 Farg'ona Dispecherlari",
            'back': "🏠 Asosiy menyu",
            'percent_1': "🥉 1% - START",
            'percent_2': "🥈 2% - PRO",
            'percent_3_5': "🥇 3.5% - VIP"
        }
    },
    Language.RUSSIAN: {
        'choose_language': "🇺🇿 🇷🇺 Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        'welcome': (
            "👋 Здравствуйте! Добро пожаловать в бота Yengil Taxi!\n\n"
            "🚖 Здесь собраны самые удобные, доходные и надежные тарифы таксопарка для вас.\n"
            "🏆 У нас есть 3 высокоуровневых тарифа — каждый со своими преимуществами, бонусами "
            "и возможностями стабильного дохода.\n\n"
            "ℹ️ С каким тарифом или информацией вы хотите ознакомиться? Выберите ниже:"
        ),
        'main_menu': "🏠 **Главное меню:**\n\nВыберите нужный раздел и начните увеличивать свой доход!",
        'please_select': "Пожалуйста, выберите нужный раздел из меню.",
        'about_taxipark': (
            "🏆Yengil TAXI - Это Надежность и Стабильный Доход!\n\n"
            "✨ *Почему выбирают нас?*\n\n"
            "✅ Самые дешевые проценты в городе\n"
            "✅ Техническая и диспетчерская поддержка 24/7\n"
            "✅ Бонусы таксопарка\n"
            "✅ Удобное пополнение и вывод средств\n\n"
            "💰 *Увеличьте свой доход:*\n"
            "• Доход в день: 500,000 сум\n"
            "• Бонусы и программы поощрения\n"
            "• Дополнительные источники дохода\n\n"
            "🎯 *Наша цель:*\n"
            "Сделать наших водителей стабильными и высокодоходными партнерами!"
        ),
        'percentages_menu': (
            "🚗 **Выберите тарифы:**\n\n"
            "Каждый тариф имеет специальные привилегии и преимущества. "
            "Выберите подходящий вам тариф и увеличьте свой доход!"
        ),
        'dispatcher_info': (
            "📞 **Связь с диспетчером**\n\n"
            "Вы можете связаться с нашими диспетчерами по следующим городам.\n"
            "Выберите нужный город и перейдите в его Telegram аккаунт:"
        ),
        'kokand_dispatcher': (
            "🏙️ Диспетчеры Коканда\n\n"
            "Наши диспетчеры по городу Коканд:\n\n"
            "📱 Телефон: +998 90 509 00 90\n"
            "📧 Telegram: @yengiltaxi_reg\n\n"
            "🕐 Время работы: 08:00 - 22:00\n"
            "📍 Адрес: Коканд, Алишера Навоий 12A\n\n"
            "✅ Услуги: \n"
            "• Регистрация водителей\n"
            "• Технические вопросы\n"
            "• Оплата и расчеты\n"
            "• Важные новости\n\n"
            "Для связи напишите в один из Telegram аккаунтов выше!"
        ),
        'andijan_dispatcher': (
            "🏙️ Диспетчеры Андижана\n\n"
            "Наши диспетчеры по городу Андижан:\n\n"
            "📱 Телефон: +998 33 508 00 90\n"
            "📧 Telegram: @yandexgo_andijon60\n\n"
            "🕐 Время работы: 08:00 - 22:00 \n"
            "📍 Адрес: проспект Бабура, Андижан, 222 маршрут ✅\n\n"
            "✅ Услуги: \n"
            "• Регистрация водителей\n"
            "• Технические вопросы\n"
            "• Оплата и расчеты\n"
            "• Важные новости\n\n"
            "Для связи напишите в один из Telegram аккаунтов выше!"
        ),
        'fergana_dispatcher': (
            "🏙️ Диспетчеры Ферганы\n\n"
            "Наши диспетчеры по городу Фергана:\n\n"
            "📱 Телефон: +998 33 509 00 90\n"
            "📧 Telegram: @yandexgo_fergana\n\n"
            "🕐 Время работы: 08:00 - 22:00\n"
            "📍 Адрес: Фергана,\n\n"
            "✅ Услуги: \n"
            "• Прием водителей\n"
            "• Аэропорт трансферы\n"
            "• Корпоративные клиенты\n"
            "• Премиум услуги\n\n"
            "Для связи напишите в один из Telegram аккаунтов выше!"
        ),
        'percent_1_info': (
            "🥉 *ТАРИФ START - 1%*\n"
            "_(Начальный уровень)_\n\n"
            "💰 *Возможности дохода:*\n"
            "• *Дневной доход:* 200,000 - 400,000 сум\n"
            "• *Комиссия:* Всего **1%**\n\n"
            "💡 *Идеально для:* Новичков\n\n"
            "🔥 *Чтобы начать:* нажмите кнопку ниже!"
        ),
        'percent_2_info': (
            "🥈 *ТАРИФ PRO - 2%*\n"
            "_(Профессиональный уровень)_\n\n"
            
            "💰 *Возможности дохода:*\n"
            "• *Месячный доход:* 300,000 - 500,000 сум\n"
            "• *Комиссия:* Всего **2%** (оптимальное соотношение!)\n"
            "• *Оплата:* Каждое воскресенье\n"
            "• *Бонус:* **10% Кэшбек**\n\n"
            
            "Отличный выбор для опытных водителей и тех, кто ищет стабильный высокий доход!\n\n"
            
            "🔥 *Стать профессионалом:* нажмите кнопку ниже!"
        ),
        'percent_3_5_info': (
            "🥇 *ТАРИФ VIP - 3.5%*\n"
            "_(Элитный уровень)_\n\n"
            
            "💰 *Элитные доходы:*\n"
            "• *Дневной доход:* 400,000 - 600,000 сум\n"
            "• *Комиссия:* Всего **3.5%** (самое выгодное для высокого дохода!)\n"
            "• *Бонус:* Специальные бонусы от Yandex на 1-2 недели\n\n"
            
            "Отличный выбор для элитных водителей, желающих предоставлять высококачественные услуги "
            "и стремящихся к высокому доходу!\n\n"
            
            "🔥 *Присоединиться к элите:* нажмите кнопку ниже!"
        ),
        'buttons': {
            'about': "О Таксопарке🧾",
            'percentages': "Проценты Таксопарка📊",
            'dispatcher': "Связь с Диспетчером📞",
            'kokand': "📍 Диспетчеры Коканда",
            'andijan': "📍 Диспетчеры Андижана",
            'fergana': "📍 Диспетчеры Ферганы",
            'back': "🏠 Главное меню",
            'percent_1': "🥉 1% - START",
            'percent_2': "🥈 2% - PRO",
            'percent_3_5': "🥇 3.5% - VIP"
        }
    }
}

def send_with_example_photo(chat_id, text, photo_path):
    """Отправляет сообщение с примером фото"""
    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=text, timeout=30)
        else:
            bot.send_message(chat_id, text + "\n\n(Пример фото временно недоступен)", timeout=30)
    except Exception as e:
        logger.error(f"Ошибка отправки фото {photo_path}: {e}")
        try:
            bot.send_message(chat_id, text, timeout=30)
        except:
            pass

def send_approval_request(user_id, phone_number, username):
    """Отправляет заявку админу на одобрение со всеми фото и информацией о тарифе"""
    try:
        # Получаем выбранный тариф пользователя
        selected_tariff = user_data[user_id].get('selected_tariff', 'Tarif tanlanmagan')
        tariff_description = user_data[user_id].get('tariff_description', '')
        
        # Формируем текстовое сообщение для админа
        admin_message = (
            "📋 Новая заявка на регистрацию:\n\n"
            f"📱 Номер телефона: {phone_number}\n"
            f"👤 Telegram: {username}\n"
            f"🆔 ID пользователя: {user_id}\n"
            f"📛 Имя: {user_data[user_id].get('first_name', 'Не указано')}\n"
            f"📛 Фамилия: {user_data[user_id].get('last_name', 'Не указано')}\n"
            f"🚗 Выбранный тариф: {selected_tariff}\n"
            f"📊 О тарифе: {tariff_description}"
        )
        
        # Создаем кнопки для одобрения и отказа
        markup = types.InlineKeyboardMarkup()
        approve_button = types.InlineKeyboardButton(
            "✅ Подтвердить", 
            callback_data=f"approve_{user_id}_{phone_number}"
        )
        reject_button = types.InlineKeyboardButton(
            "❌ Отклонить", 
            callback_data=f"reject_{user_id}_{phone_number}"
        )
        markup.add(approve_button, reject_button)
        
        # Сначала отправляем текстовое сообщение с кнопками
        text_msg = bot.send_message(ADMIN_ID, admin_message, reply_markup=markup, timeout=30)
        
        # Сохраняем информацию о заявке
        pending_approvals[user_id] = {
            'phone_number': phone_number,
            'username': username,
            'admin_message_id': text_msg.message_id,
            'tariff': selected_tariff
        }
        
        # Отправляем все фото пользователя админу
        photo_descriptions = [
            ('license_front', '📄 Лицевая сторона водительского удостоверения'),
            ('license_back', '📄 Обратная сторона водительского удостоверения'),
            ('passport_front', '📋 Лицевая сторона техпаспорта'),
            ('passport_back', '📋 Обратная сторона техпаспорта')
        ]
        
        for photo_key, description in photo_descriptions:
            if photo_key in user_data[user_id]:
                file_id = user_data[user_id][photo_key]['file_id']
                try:
                    bot.send_photo(ADMIN_ID, file_id, caption=description, timeout=30)
                except Exception as e:
                    logger.error(f"Ошибка отправки фото {photo_key} администратору: {e}")
        
        logger.info(f"Заявка пользователя {user_id} отправлена администратору {ADMIN_ID}")
        logger.info(f"Выбранный тариф пользователя: {selected_tariff}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки заявки администратору: {e}")

def send_approval_to_user(user_id):
    """Отправляет пользователю сообщение об одобрении с картинкой"""
    try:
        lang = get_user_language(user_id)
        
        if lang == Language.UZBEK:
            approval_message = (
                "🎉 Tabriklaymiz! Sizning arizangiz tasdiqlangan!\n\n"
                "Endi siz boshlashingiz mumkin. "
                "Taksi xizmatimizni tanlaganingiz uchun tashakkur!"
            )
        else:
            approval_message = (
                "🎉 Поздравляем! Ваша заявка подтверждена!\n\n"
                "Теперь вы можете начать работу. "
                "Спасибо, что выбрали нашу такси-службу!"
            )
        
        # Пытаемся отправить с картинкой
        if os.path.exists('driver_photo/accept_photo.jpg'):
            with open('driver_photo/accept_photo.jpg', 'rb') as photo:
                bot.send_photo(user_id, photo, caption=approval_message, timeout=30)
        else:
            # Если картинки нет, отправляем только текст
            bot.send_message(user_id, approval_message, timeout=30)
            
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения подтверждения пользователю {user_id}: {e}")
        # Если ошибка, пробуем отправить просто текст
        try:
            if get_user_language(user_id) == Language.UZBEK:
                bot.send_message(user_id, "🎉 Tabriklaymiz! Sizning arizangiz tasdiqlangan!", timeout=30)
            else:
                bot.send_message(user_id, "🎉 Поздравляем! Ваша заявка подтверждена!", timeout=30)
        except Exception as e2:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e2}")

def send_rejection_to_user(user_id):
    """Отправляет пользователю сообщение об отказе с картинкой"""
    try:
        lang = get_user_language(user_id)
        
        if lang == Language.UZBEK:
            rejection_message = (
                "MA'LUMOTLARINGIZDA XATOLAR MAVJUD\n"
                "BIZNING DISPETCHERLARIMIZ SIZ BILAN BOG'LANISHADI ⏳"
            )
        else:
            rejection_message = (
                "В ВАШИХ ДАННЫХ ИМЕЮТСЯ ОШИБКИ\n"
                "НАШИ ДИСПЕТЧЕРЫ СВЯЖУТСЯ С ВАМИ ⏳"
            )
        
        # Пытаемся отправить с картинкой
        if os.path.exists('driver_photo/otkaz_photo.jpg'):
            with open('driver_photo/otkaz_photo.jpg', 'rb') as photo:
                bot.send_photo(user_id, photo, caption=rejection_message, timeout=30)
        else:
            # Если картинки нет, отправляем только текст
            bot.send_message(user_id, rejection_message, timeout=30)
            
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения об отказе пользователю {user_id}: {e}")
        # Если ошибка, пробуем отправить просто текст
        try:
            if get_user_language(user_id) == Language.UZBEK:
                bot.send_message(user_id, "MA'LUMOTLARINGIZDA XATOLAR MAVJUD\nBIZNING DISPETCHERLARIMIZ SIZ BILAN BOG'LANISHADI ⏳", timeout=30)
            else:
                bot.send_message(user_id, "В ВАШИХ ДАННЫХ ИМЕЮТСЯ ОШИБКИ\nНАШИ ДИСПЕТЧЕРЫ СВЯЖУТСЯ С ВАМИ ⏳", timeout=30)
        except Exception as e2:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e2}")

# Команда для получения ID
@bot.message_handler(commands=['getid'])
def get_id(message):
    """Показывает ID пользователя"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ''
    last_name = message.from_user.last_name or ''
    username = message.from_user.username or "Ko'rsatilmagan / Не указано"
    
    response = (
        f"📋 Ваши данные:\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Имя: {first_name} {last_name}\n"
        f"📱 Username: @{username}"
    )
    
    try:
        bot.send_message(message.chat.id, response, timeout=30)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    user_data[user_id] = {
        'state': RegistrationState.LANGUAGE_SELECTION,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name
    }
    
    # Предлагаем выбрать язык
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    uz_button = types.KeyboardButton("🇺🇿 O'zbekcha")
    ru_button = types.KeyboardButton("🇷🇺 Русский")
    markup.add(uz_button, ru_button)
    
    try:
        bot.send_message(message.chat.id, TEXTS[Language.UZBEK]['choose_language'], reply_markup=markup, timeout=30)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения выбора языка: {e}")

@bot.message_handler(func=lambda message: message.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"])
def handle_language_selection(message):
    """Обработчик выбора языка"""
    user_id = message.from_user.id
    
    if message.text == "🇺🇿 O'zbekcha":
        user_data[user_id]['language'] = Language.UZBEK
        lang = Language.UZBEK
    else:
        user_data[user_id]['language'] = Language.RUSSIAN
        lang = Language.RUSSIAN
    
    user_data[user_id]['state'] = RegistrationState.START
    
    texts = TEXTS[lang]
    
    # Создаем главное меню на выбранном языке
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    about_button = types.KeyboardButton(texts['buttons']['about'])
    percentage_button = types.KeyboardButton(texts['buttons']['percentages'])
    dispatcher_button = types.KeyboardButton(texts['buttons']['dispatcher'])
    markup.add(about_button, percentage_button, dispatcher_button)
    
    try:
        bot.send_message(message.chat.id, texts['welcome'], reply_markup=markup, timeout=30)
    except Exception as e:
        logger.error(f"Ошибка отправки приветственного сообщения: {e}")

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == RegistrationState.START)
def handle_main_menu(message):
    """Обработчик главного меню"""
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    texts = TEXTS[lang]
    
    if message.text == texts['buttons']['about']:
        info_text = texts['about_taxipark']
        
        with open("logo_yengil.jpg", "rb") as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption=info_text,
                parse_mode="Markdown"
            )
    
    elif message.text == texts['buttons']['percentages']:
        # Создаем подменю для выбора процентов
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        percent_1 = types.KeyboardButton(texts['buttons']['percent_1'])
        percent_2 = types.KeyboardButton(texts['buttons']['percent_2'])
        percent_3_5 = types.KeyboardButton(texts['buttons']['percent_3_5'])
        back_button = types.KeyboardButton(texts['buttons']['back'])
        markup.add(percent_1, percent_2, percent_3_5, back_button)
        
        try:
            bot.send_message(
                message.chat.id,
                texts['percentages_menu'],
                reply_markup=markup,
                parse_mode='Markdown',
                timeout=30
            )
        except Exception as e:
            logger.error(f"Ошибка отправки меню процентов: {e}")
    
    elif message.text == texts['buttons']['dispatcher']:
        dispatcher_info = texts['dispatcher_info']
        
        # Создаем меню выбора диспетчеров
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kokand_button = types.KeyboardButton(texts['buttons']['kokand'])
        andijan_button = types.KeyboardButton(texts['buttons']['andijan'])
        fergana_button = types.KeyboardButton(texts['buttons']['fergana'])
        back_button = types.KeyboardButton(texts['buttons']['back'])
        markup.add(kokand_button, andijan_button, fergana_button, back_button)
        
        try:
            bot.send_message(
                message.chat.id,
                dispatcher_info,
                reply_markup=markup,
                parse_mode='Markdown',
                timeout=30
            )
        except Exception as e:
            logger.error(f"Ошибка отправки меню диспетчеров: {e}")
    
    elif message.text == texts['buttons']['back']:
        # Возврат в главное меню
        user_data[user_id] = {
            'state': RegistrationState.START,
            'language': lang,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        about_button = types.KeyboardButton(texts['buttons']['about'])
        percentage_button = types.KeyboardButton(texts['buttons']['percentages'])
        dispatcher_button = types.KeyboardButton(texts['buttons']['dispatcher'])
        markup.add(about_button, percentage_button, dispatcher_button)
        
        try:
            bot.send_message(message.chat.id, texts['main_menu'], reply_markup=markup, parse_mode='Markdown', timeout=30)
        except Exception as e:
            logger.error(f"Ошибка отправки главного меню: {e}")
    
    elif message.text == texts['buttons']['kokand']:
        dispatcher_text = texts['kokand_dispatcher']
        
        # Создаем inline-кнопки
        markup = types.InlineKeyboardMarkup(row_width=1)
        contact_button = types.InlineKeyboardButton(
            "📱 Связаться / Aloqaga chiqish",
            url="https://t.me/yengiltaxi_reg"
        )
        location_button = types.InlineKeyboardButton(
            "📍 Посмотреть локацию / Lokatsiyani ko'rish",
            url="https://maps.app.goo.gl/1e7sR8gQHjtbpp9DA?g_st=ac"
        )
        markup.add(contact_button, location_button)

        # Отправляем фото вместе с текстом и кнопкой
        try:
            photo_path = 'qoqon_dispecher.jpg'
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=photo,
                        caption=dispatcher_text,
                        reply_markup=markup,
                        timeout=30
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    dispatcher_text,
                    reply_markup=markup,
                    timeout=30
                )
        except Exception as e:
            logger.error(f"Ошибка отправки информации о диспетчерах Коканда: {e}")
    
    elif message.text == texts['buttons']['andijan']:
        dispatcher_text = texts['andijan_dispatcher']
        
        # Создаем inline-кнопки для быстрого перехода
        markup = types.InlineKeyboardMarkup(row_width=1)
        contact_button = types.InlineKeyboardButton(
            "📱 Связаться / Aloqaga chiqish",
            url="https://t.me/yandexgo_andijon60"
        )
        location_button = types.InlineKeyboardButton(
            "📍 Посмотреть локацию / Lokatsiyani ko'rish",
            url="https://maps.app.goo.gl/UhHzMXG5rvbXRJK69?g_st=ac"
        )
        markup.add(contact_button, location_button)
        
        try:
            photo_path = 'andijan_dispecher.jpg'
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=dispatcher_text,
                        reply_markup=markup,
                        timeout=30
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    dispatcher_text,
                    reply_markup=markup,
                    timeout=30
                )
        except Exception as e:
            logger.error(f"Ошибка отправки информации о диспетчерах Андижана: {e}")
    
    elif message.text == texts['buttons']['fergana']:
        dispatcher_text = texts['fergana_dispatcher']
        
        # Создаем inline-кнопки для быстрого перехода
        markup = types.InlineKeyboardMarkup(row_width=1)
        contact_button = types.InlineKeyboardButton(
            "📱 Связаться / Aloqaga chiqish", 
            url="https://t.me/yandexgo_fergana"
        )
        location_button = types.InlineKeyboardButton(
            "📍 Посмотреть локацию / Lokatsiyani ko'rish",
            url="https://maps.app.goo.gl/esN9rac8tSzrQFe96?g_st=ac"
        )
        markup.add(contact_button, location_button)
        
        try:
            photo_path = 'Fargana_Dispecher.jpg'
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=dispatcher_text,
                        reply_markup=markup,
                        timeout=30
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    dispatcher_text,
                    reply_markup=markup,
                    timeout=30
                )
        except Exception as e:
            logger.error(f"Ошибка отправки информации о диспетчерах Ферганы: {e}")
    
    elif message.text == texts['buttons']['percent_1']:
        user_id = message.from_user.id
        
        # Сохраняем выбранный тариф для пользователя
        lang = get_user_language(user_id)
        if lang == Language.UZBEK:
            user_data[user_id]['selected_tariff'] = "START (1%)"
            user_data[user_id]['tariff_description'] = "Boshlang'ich daraja - Kunlik daromad: 200,000 - 400,000 so'm"
        else:
            user_data[user_id]['selected_tariff'] = "START (1%)"
            user_data[user_id]['tariff_description'] = "Начальный уровень - Дневной доход: 200,000 - 400,000 сум"

        info_text = texts['percent_1_info']

        # Создаем кнопку для регистрации
        markup = types.InlineKeyboardMarkup()
        if lang == Language.UZBEK:
            register_button = types.InlineKeyboardButton("🚀 Ro'yxatdan o'tish", callback_data="start_registration_from_tariff")
        else:
            register_button = types.InlineKeyboardButton("🚀 Зарегистрироваться", callback_data="start_registration_from_tariff")
        markup.add(register_button)
        
        try:
            with open("1prosent.jpg", "rb") as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=info_text,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки фото тарифа 1%: {e}")
            try:
                bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode='Markdown', timeout=30)
            except Exception as e2:
                logger.error(f"Ошибка отправки сообщения тарифа 1%: {e2}")
    
    elif message.text == texts['buttons']['percent_2']:
        user_id = message.from_user.id
        
        # Сохраняем выбранный тариф для пользователя
        lang = get_user_language(user_id)
        if lang == Language.UZBEK:
            user_data[user_id]['selected_tariff'] = "PRO (2%)"
            user_data[user_id]['tariff_description'] = "Professional daraja - Oylik daromad: 300,000 - 500,000 so'm, 10% Keshbek"
        else:
            user_data[user_id]['selected_tariff'] = "PRO (2%)"
            user_data[user_id]['tariff_description'] = "Профессиональный уровень - Месячный доход: 300,000 - 500,000 сум, 10% Кэшбек"

        info_text = texts['percent_2_info']

        # Создаем кнопку для регистрации
        markup = types.InlineKeyboardMarkup()
        if lang == Language.UZBEK:
            register_button = types.InlineKeyboardButton("🚀 Ro'yxatdan o'tish", callback_data="start_registration_from_tariff")
        else:
            register_button = types.InlineKeyboardButton("🚀 Зарегистрироваться", callback_data="start_registration_from_tariff")
        markup.add(register_button)
        
        try:
            with open("2prosent.png", "rb") as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=info_text,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки фото тарифа 2%: {e}")
            try:
                bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode='Markdown', timeout=30)
            except Exception as e2:
                logger.error(f"Ошибка отправки сообщения тарифа 2%: {e2}")
    
    elif message.text == texts['buttons']['percent_3_5']:
        user_id = message.from_user.id
        
        # Сохраняем выбранный тариф для пользователя
        lang = get_user_language(user_id)
        if lang == Language.UZBEK:
            user_data[user_id]['selected_tariff'] = "VIP (3.5%)"
            user_data[user_id]['tariff_description'] = "Elita daraja - Kunlik daromad: 400,000 - 600,000 so'm, Yandex bonuslari"
        else:
            user_data[user_id]['selected_tariff'] = "VIP (3.5%)"
            user_data[user_id]['tariff_description'] = "Элитный уровень - Дневной доход: 400,000 - 600,000 сум, Бонусы от Yandex"

        info_text = texts['percent_3_5_info']

        # Создаем кнопку для регистрации
        markup = types.InlineKeyboardMarkup()
        if lang == Language.UZBEK:
            register_button = types.InlineKeyboardButton("🚀 Ro'yxatdan o'tish", callback_data="start_registration_from_tariff")
        else:
            register_button = types.InlineKeyboardButton("🚀 Зарегистрироваться", callback_data="start_registration_from_tariff")
        markup.add(register_button)
        
        try:
            with open("3.5prosent.png", "rb") as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=info_text,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
        except Exception as e:
            logger.error(f"Ошибка отправки фото тарифа 3.5%: {e}")
            try:
                bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode='Markdown', timeout=30)
            except Exception as e2:
                logger.error(f"Ошибка отправки сообщения тарифа 3.5%: {e2}")
    
    else:
        try:
            bot.send_message(message.chat.id, texts['please_select'], timeout=30)
        except:
            pass

# Обработчик для всех фото
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """Обрабатывает все фотографии"""
    user_id = message.from_user.id
    current_state = get_user_state(user_id)
    
    if current_state == RegistrationState.LICENSE_FRONT:
        handle_license_front(message)
    elif current_state == RegistrationState.LICENSE_BACK:
        handle_license_back(message)
    elif current_state == RegistrationState.PASSPORT_FRONT:
        handle_passport_front(message)
    elif current_state == RegistrationState.PASSPORT_BACK:
        handle_passport_back(message)
    else:
        lang = get_user_language(user_id)
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Iltimos, ro'yxatdan o'tish ko'rsatmalariga amal qiling.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, следуйте инструкциям по регистрации.", timeout=30)
        except:
            pass

def handle_license_front(message):
    """Обрабатывает лицевую сторону водительского удостоверения"""
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    try:
        # Сохраняем информацию о фото во временные данные
        file_info = bot.get_file(message.photo[-1].file_id)
        user_data[user_id]['license_front'] = {
            'file_path': file_info.file_path,
            'file_id': message.photo[-1].file_id
        }
        
        # Меняем состояние
        user_data[user_id]['state'] = RegistrationState.LICENSE_BACK
        
        # Отправляем пример фото обратной стороны прав сразу с текстом
        if lang == Language.UZBEK:
            example_text = (
                "✅ **Qabul qilindi!** Ajoyib ish!\n\n"
                "📸 **2-qadam:** Haydovchilik guvohnomasining orqa tomoni\n\n"
                "Endi haydovchilik guvohnomangizning orqa tomonini yuboring.\n\n"
                "Misol fotosurat qanday ko'rinishi kerak:"
            )
        else:
            example_text = (
                "✅ **Принято!** Отличная работа!\n\n"
                "📸 **2-й шаг:** Обратная сторона водительского удостоверения\n\n"
                "Теперь отправьте обратную сторону вашего водительского удостоверения.\n\n"
                "Как должен выглядеть пример фото:"
            )
        
        send_with_example_photo(message.chat.id, example_text, 'driver_photo/driver_license_back.jpg')
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Xato yuz berdi. Iltimos, fotosuratni yana yuboring.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, отправьте фото еще раз.", timeout=30)
        except:
            pass

def handle_license_back(message):
    """Обрабатывает обратную сторону водительского удостоверения"""
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    try:
        # Сохраняем информацию о фото во временные данные
        file_info = bot.get_file(message.photo[-1].file_id)
        user_data[user_id]['license_back'] = {
            'file_path': file_info.file_path,
            'file_id': message.photo[-1].file_id
        }
        
        # Меняем состояние
        user_data[user_id]['state'] = RegistrationState.PASSPORT_FRONT
        
        # Отправляем пример фото лицевой стороны техпаспорта сразу с текстом
        if lang == Language.UZBEK:
            example_text = (
                "✅ **Qabul qilindi!** Juda yaxshi!\n\n"
                "📸 **3-qadam:** Texnik pasportning old tomoni\n\n"
                "Endi texnik pasportingizning old tomonini yuboring.\n\n"
                "Misol fotosurat qanday ko'rinishi kerak:"
            )
        else:
            example_text = (
                "✅ **Принято!** Очень хорошо!\n\n"
                "📸 **3-й шаг:** Лицевая сторона техпаспорта\n\n"
                "Теперь отправьте лицевую сторону вашего техпаспорта.\n\n"
                "Как должен выглядеть пример фото:"
            )
        
        send_with_example_photo(message.chat.id, example_text, 'driver_photo/tech_passport_front.jpg')
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Xato yuz berdi. Iltimos, fotosuratni yana yuboring.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, отправьте фото еще раз.", timeout=30)
        except:
            pass

def handle_passport_front(message):
    """Обрабатывает лицевую сторону техпаспорта"""
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    try:
        # Сохраняем информацию о фото во временные данные
        file_info = bot.get_file(message.photo[-1].file_id)
        user_data[user_id]['passport_front'] = {
            'file_path': file_info.file_path,
            'file_id': message.photo[-1].file_id
        }
        
        # Меняем состояние
        user_data[user_id]['state'] = RegistrationState.PASSPORT_BACK
        
        # Отправляем пример фото обратной стороны техпаспорта сразу с текстом
        if lang == Language.UZBEK:
            example_text = (
                "✅ **Qabul qilindi!** Faqat bir qadam qoldi!\n\n"
                "📸 **4-qadam:** Texnik pasportning orqa tomoni\n\n"
                "Endi texnik pasportingizning orqa tomonini yuboring.\n\n"
                "Misol fotosurat qanday ko'rinishi kerak:"
            )
        else:
            example_text = (
                "✅ **Принято!** Остался только один шаг!\n\n"
                "📸 **4-й шаг:** Обратная сторона техпаспорта\n\n"
                "Теперь отправьте обратную сторону вашего техпаспорта.\n\n"
                "Как должен выглядеть пример фото:"
            )
        
        send_with_example_photo(message.chat.id, example_text, 'driver_photo/tech_passport_back.jpg')
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Xato yuz berdi. Iltimos, fotosuratni yana yuboring.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, отправьте фото еще раз.", timeout=30)
        except:
            pass

def handle_passport_back(message):
    """Обрабатывает обратную сторону техпаспорта"""
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    try:
        # Сохраняем информацию о фото во временные данные
        file_info = bot.get_file(message.photo[-1].file_id)
        user_data[user_id]['passport_back'] = {
            'file_path': file_info.file_path,
            'file_id': message.photo[-1].file_id
        }
        
        # Меняем состояние
        user_data[user_id]['state'] = RegistrationState.PHONE
        
        # Создаем кнопку для отправки номера телефона
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if lang == Language.UZBEK:
            phone_button = types.KeyboardButton("📱 Telefon raqamini yuboring", request_contact=True)
        else:
            phone_button = types.KeyboardButton("📱 Отправить номер телефона", request_contact=True)
        markup.add(phone_button)
        
        if lang == Language.UZBEK:
            text = (
                "🎉 **Barcha hujjatlar qabul qilindi!**\n\n"
                f"📊 **Sizning tanlovingiz:** {user_data[user_id].get('selected_tariff', 'Tarif tanlanmagan')}\n\n"
                "🏆 **Oxirgi qadam:** Telefon raqamingiz\n\n"
                "Ro'yxatdan o'tishni yakunlash uchun telefon raqamingizni yuboring. "
                "Bu biz siz bilan bog'lanishimiz uchun zarur."
            )
        else:
            text = (
                "🎉 **Все документы приняты!**\n\n"
                f"📊 **Ваш выбор:** {user_data[user_id].get('selected_tariff', 'Тариф не выбран')}\n\n"
                "🏆 **Последний шаг:** Ваш номер телефона\n\n"
                "Для завершения регистрации отправьте ваш номер телефона. "
                "Это необходимо для связи с вами."
            )
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='Markdown',
            timeout=30
        )
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Xato yuz berdi. Iltimos, fotosuratni yana yuboring.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, отправьте фото еще раз.", timeout=30)
        except:
            pass

# Обработчик для контактов
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Обрабатывает номер телефона"""
    user_id = message.from_user.id
    current_state = get_user_state(user_id)
    
    if current_state == RegistrationState.PHONE:
        handle_phone(message)
    else:
        lang = get_user_language(user_id)
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Iltimos, avval hujjatlarni yuborishni yakunlang.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, сначала завершите отправку документов.", timeout=30)
        except:
            pass

def handle_phone(message):
    """Обрабатывает номер телефона и сохраняет все данные"""
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    try:
        phone_number = message.contact.phone_number
        
        # Добавляем + если его нет
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        # Получаем username пользователя
        username = user_data[user_id].get('username', "Ko'rsatilmagan / Не указано")
        selected_tariff = user_data[user_id].get('selected_tariff', 'Tarif tanlanmagan / Тариф не выбран')
        
        # Создаем папку для пользователя
        user_folder = os.path.join(DATA_FOLDER, phone_number)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Сохраняем все фотографии
        photos_to_save = [
            ('license_front', 'driver_license_front.jpg'),
            ('license_back', 'driver_license_back.jpg'),
            ('passport_front', 'tech_passport_front.jpg'),
            ('passport_back', 'tech_passport_back.jpg')
        ]
        
        success_count = 0
        for photo_key, filename in photos_to_save:
            if photo_key in user_data[user_id]:
                file_data = user_data[user_id][photo_key]
                try:
                    downloaded_file = bot.download_file(file_data['file_path'])
                    
                    save_path = os.path.join(user_folder, filename)
                    with open(save_path, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    success_count += 1
                    logger.info(f"Сохранен файл: {save_path}")
                except Exception as e:
                    logger.error(f"Ошибка сохранения {photo_key}: {e}")
        
        # Сохраняем информацию о пользователе в текстовый файл
        user_info_path = os.path.join(user_folder, 'user_info.txt')
        with open(user_info_path, 'w', encoding='utf-8') as f:
            f.write(f"Телефон: {phone_number}\n")
            f.write(f"Telegram: {username}\n")
            f.write(f"ID: {user_id}\n")
            f.write(f"Имя: {message.from_user.first_name or 'Не указано'}\n")
            f.write(f"Фамилия: {message.from_user.last_name or 'Не указано'}\n")
            f.write(f"Выбранный тариф: {selected_tariff}\n")
            f.write(f"О тарифе: {user_data[user_id].get('tariff_description', '')}\n")
        
        # Отправляем сообщение пользователю
        if lang == Language.UZBEK:
            user_message = (
                f"✅ **Sizning identifikatoringiz va hujjatlaringiz administratorga yuborilgan!**\n\n"
                f"📊 **Sizning tanlovingiz:** {selected_tariff}\n\n"
                "Ish tasdiqlanishini kuting...\n\n"
                "Admin sizni tez orada tasdiqlaydi.\n\n"
                "🎯 **Sizning daromadingiz boshlanishiga faqat bir necha daqiqa qoldi!**"
            )
        else:
            user_message = (
                f"✅ **Ваши данные и документы отправлены администратору!**\n\n"
                f"📊 **Ваш выбор:** {selected_tariff}\n\n"
                "Ожидайте подтверждения работы...\n\n"
                "Администратор подтвердит вас в ближайшее время.\n\n"
                "🎯 **До начала вашего заработка осталось всего несколько минут!**"
            )
        
        # Убираем клавиатуру
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, user_message, reply_markup=markup, parse_mode='Markdown', timeout=30)
        
        # Отправляем заявку админу (включая информацию о тарифе)
        send_approval_request(user_id, phone_number, username)
        
        logger.info(f"Пользователь {user_id} ({username}) отправил заявку с номером {phone_number}")
        logger.info(f"Выбранный тариф: {selected_tariff}")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Ma'lumotlarni saqlashda xatolik yuz berdi. Iltimos, ro'yxatdan o'tishni qayta boshlang.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных. Пожалуйста, начните регистрацию заново.", timeout=30)
        except:
            pass

# Обработчик callback-ов от кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обрабатывает нажатия на inline-кнопки"""
    try:
        if call.data.startswith('approve_'):
            # Разбираем callback_data: approve_userId_phoneNumber
            parts = call.data.split('_')
            if len(parts) >= 3:
                user_id = int(parts[1])
                phone_number = '_'.join(parts[2:])  # На случай если номер содержит _
                
                # Отправляем сообщение пользователю об одобрении с картинкой
                send_approval_to_user(user_id)
                
                # Получаем информацию о тарифе
                tariff_info = ""
                if user_id in pending_approvals:
                    tariff_info = f"\n🚗 Выбранный тариф: {pending_approvals[user_id].get('tariff', 'Неизвестно')}"
                
                # Обновляем сообщение админу
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ Заявка подтверждена:\n{call.message.text}{tariff_info}\n\nСтатус: подтверждено ✅"
                )
                
                # Удаляем из ожидающих одобрения
                if user_id in pending_approvals:
                    del pending_approvals[user_id]
                
                logger.info(f"Заявка пользователя {user_id} подтверждена администратором")
        
        elif call.data.startswith('reject_'):
            # Разбираем callback_data: reject_userId_phoneNumber
            parts = call.data.split('_')
            if len(parts) >= 3:
                user_id = int(parts[1])
                phone_number = '_'.join(parts[2:])  # На случай если номер содержит _
                
                # Отправляем сообщение пользователю об отказе с картинкой
                send_rejection_to_user(user_id)
                
                # Получаем информацию о тарифе
                tariff_info = ""
                if user_id in pending_approvals:
                    tariff_info = f"\n🚗 Выбранный тариф: {pending_approvals[user_id].get('tariff', 'Неизвестно')}"
                
                # Обновляем сообщение админу
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"❌ Заявка отклонена:\n{call.message.text}{tariff_info}\n\nСтатус: отклонено ❌"
                )
                
                # Удаляем из ожидающих одобрения
                if user_id in pending_approvals:
                    del pending_approvals[user_id]
                
                logger.info(f"Заявка пользователя {user_id} отклонена администратором")
        
        elif call.data in ["register_from_percent1", "register_from_percent2", "register_from_percent3"]:
            # Обработка старых кнопок регистрации (оставлено для совместимости)
            try:
                # Определяем какой процент был выбран
                if call.data == "register_from_percent1":
                    selected_plan = "START (1%)"
                    tariff_desc = "Boshlang'ich daraja - Kunlik daromad: 200,000 - 400,000 so'm"
                elif call.data == "register_from_percent2":
                    selected_plan = "PRO (2%)"
                    tariff_desc = "Professional daraja - Oylik daromad: 300,000 - 500,000 so'm, 10% Keshbek"
                else:
                    selected_plan = "VIP (3.5%)"
                    tariff_desc = "Elita daraja - Kunlik daromad: 400,000 - 600,000 so'm, Yandex bonuslari"
                
                # Сохраняем тариф для пользователя
                user_id = call.from_user.id
                user_data[user_id]['selected_tariff'] = selected_plan
                user_data[user_id]['tariff_description'] = tariff_desc
                
                # Отправляем сообщение
                response_text = (
                    f"✅ **{selected_plan} tarifini tanladingiz!**\n\n"
                    "Ajoyib tanlov! Bu tarif bilan yuqori daromadlar sizni kutmoqda.\n\n"
                    "Ro'yxatdan o'tishni boshlash uchun quyidagi tugmani bosing:"
                )
                
                # Создаем кнопку для начала регистрации
                markup = types.InlineKeyboardMarkup()
                start_reg = types.InlineKeyboardButton("🚀 Ro'yxatdan o'tishni boshlash", callback_data="start_registration_now")
                markup.add(start_reg)
                
                bot.edit_message_text(
                    response_text,
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                
                bot.answer_callback_query(call.id, f"{selected_plan} tarifini tanladingiz!")
            except Exception as e:
                logger.error(f"Ошибка обработки callback: {e}")
                bot.answer_callback_query(call.id, "Произошла ошибка")
            return
            
        elif call.data == "start_registration_now" or call.data == "start_registration_from_tariff":
            # Обработка кнопки начала регистрации
            try:
                user_id = call.from_user.id
                lang = get_user_language(user_id)
                
                # Проверяем, выбрал ли пользователь тариф
                if 'selected_tariff' not in user_data.get(user_id, {}):
                    if lang == Language.UZBEK:
                        bot.answer_callback_query(call.id, "Iltimos, avval tarifni tanlang!")
                    else:
                        bot.answer_callback_query(call.id, "Пожалуйста, сначала выберите тариф!")
                    return
                
                user_data[user_id] = user_data.get(user_id, {})
                user_data[user_id].update({
                    'state': RegistrationState.LICENSE_FRONT,
                    'username': f"@{call.from_user.username}" if call.from_user.username else "Ko'rsatilmagan / Не указано",
                    'first_name': call.from_user.first_name,
                    'last_name': call.from_user.last_name
                })
                
                # Убираем сообщение с кнопками
                bot.delete_message(call.message.chat.id, call.message.message_id)
                
                # Начинаем регистрацию
                selected_tariff = user_data[user_id].get('selected_tariff', 'Tarif tanlanmagan / Тариф не выбран')
                
                if lang == Language.UZBEK:
                    welcome_reg = (
                        "🎯 **Ro'yxatdan o'tish boshlandi!**\n\n"
                        f"✅ Siz {selected_tariff} tarifini tanladingiz!\n\n"
                        "Endi yuqori daromadga yo'l ochdingiz.\n"
                        "Quyidagi bosqichlarni bajarib, ishni boshlashingiz mumkin.\n\n"
                        "**1-qadam:** Haydovchilik guvohnomasi fotosurati"
                    )
                    example_text = (
                        "📸 **Haydovchilik guvohnomasining old tomoni**\n\n"
                        "Iltimos, aniq va yorug' fotosuratni yuboring.\n\n"
                        "Misol fotosurat qanday ko'rinishi kerak:"
                    )
                else:
                    welcome_reg = (
                        "🎯 **Регистрация началась!**\n\n"
                        f"✅ Вы выбрали тариф {selected_tariff}!\n\n"
                        "Теперь вы открыли путь к высокому доходу.\n"
                        "Выполнив следующие шаги, вы сможете начать работу.\n\n"
                        "**1-й шаг:** Фото водительского удостоверения"
                    )
                    example_text = (
                        "📸 **Лицевая сторона водительского удостоверения**\n\n"
                        "Пожалуйста, отправьте четкое и светлое фото.\n\n"
                        "Как должен выглядеть пример фото:"
                    )
                
                bot.send_message(call.message.chat.id, welcome_reg, parse_mode='Markdown', timeout=30)
                
                # Отправляем пример фото
                send_with_example_photo(call.message.chat.id, example_text, 'driver_photo/driver_license_front.jpg')
                
            except Exception as e:
                logger.error(f"Ошибка начала регистрации: {e}")
                bot.answer_callback_query(call.id, "Произошла ошибка")
            return
            
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
        try:
            bot.answer_callback_query(call.id, "Произошла ошибка")
        except:
            pass

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Обработчик всех остальных сообщений"""
    user_id = message.from_user.id
    current_state = get_user_state(user_id)
    
    if current_state == RegistrationState.LANGUAGE_SELECTION:
        # Пользователь выбирает язык
        if message.text not in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"]:
            try:
                bot.send_message(message.chat.id, TEXTS[Language.UZBEK]['choose_language'], timeout=30)
            except:
                pass
    
    elif current_state == RegistrationState.START:
        # Пользователь уже выбрал язык и в главном меню
        # Этот случай обрабатывается в handle_main_menu
        pass
    
    else:
        lang = get_user_language(user_id)
        try:
            if lang == Language.UZBEK:
                bot.send_message(message.chat.id, "Iltimos, ro'yxatdan o'tish ko'rsatmalariga amal qiling.", timeout=30)
            else:
                bot.send_message(message.chat.id, "Пожалуйста, следуйте инструкциям по регистрации.", timeout=30)
        except:
            pass

if __name__ == "__main__":
    print("Бот запущен...")
    print(f"ID администратора: {ADMIN_ID}")
    
    # Попытка переподключения при ошибках
    while True:
        try:
            print("Начато опрос бота...")
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except ReadTimeout as e:
            logger.error(f"Ошибка ReadTimeout: {e}")
            print("Проблемы с интернетом. Ожидание 5 секунд...")
            time.sleep(5)
        except ConnectionError as e:
            logger.error(f"Ошибка ConnectionError: {e}")
            print("Проблемы с соединением. Ожидание 10 секунд...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            print(f"Произошла ошибка: {e}. Ожидание 30 секунд...")
            time.sleep(30)