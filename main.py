from telethon import TelegramClient, events
from datetime import datetime
import asyncio

# === Твої дані Telegram API (з my.telegram.org) ===
api_id = 22324300
api_hash = "cf6c90f7c5140c6494e37f00dcb6dbd6"

# === ID акаунтів ===
main_user_id = 1574352010       # твій основний акаунт (з нього читаємо канали)
second_user_id = 6403321035     # твій другий акаунт (сюди надсилаємо оброблені сигнали)

# === ID каналів ===
first_channel_id = 2488924018   # Перший канал
second_channel_id = 1861059770  # Другий канал

# === Шлях до сесії (щоб не вводити номер телефону кожен раз) ===
session_path = "main_desktop_session"

# === Ініціалізація клієнта ===
client = TelegramClient(session_path, api_id, api_hash)


# Функція обробки повідомлень з першого каналу
def process_first_channel_message(message_text):
    """
    - Ігнорує відсотки з повідомлення
    - Завжди виставляє 2% від депозиту
    """
    # Прибираємо згадки про відсотки депозиту (типу "5% депо")
    import re
    cleaned_text = re.sub(r"\d+%.*депо", "", message_text, flags=re.IGNORECASE)
    # Додаємо фіксовану інфу про 2% від депозиту
    return cleaned_text.strip() + "\n💰 Обсяг: 2% від депозиту"


# Функція обробки повідомлень з другого каналу
def process_second_channel_message(message_text):
    """
    - Ігнорує шорт без стоп-лосу
    - Лонг без стопа бере
    """
    text_lower = message_text.lower()

    # Якщо це шорт без стопа — ігноруємо
    if "шорт" in text_lower and "стоп" not in text_lower:
        return None

    return message_text


# Функція обробки повідомлень про фіксацію та стоп в БУ
def process_trade_updates(message_text, channel_id):
    """
    - Розпізнає сигнали на часткову або повну фіксацію
    - Реагує на "стоп в бу"
    """
    text_lower = message_text.lower()

    # Перенос стопа в БУ
    if "стоп в бу" in text_lower:
        return "🔄 Перенос стоп-лосу в точку входу"

    # Повна фіксація
    if "фіксую повністю" in text_lower or "фиксирую полностью" in text_lower:
        return "✅ Повна фіксація позиції"

    # Часткова фіксація (50%)
    if "50%" in text_lower or "фиксирую 50%" in text_lower:
        return "📉 Часткова фіксація: 50% позиції"

    # Часткова фіксація у першому каналі (33%)
    if channel_id == first_channel_id and ("еще часть фикс" in text_lower or "ще част" in text_lower):
        return "📉 Часткова фіксація: 33% позиції"

    return None


# === Основний обробник повідомлень ===
@client.on(events.NewMessage(chats=[first_channel_id, second_channel_id]))
async def handler(event):
    try:
        original_message = event.message.message
        channel_id = event.chat_id
        channel_name = (await event.get_chat()).title
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Обробка повідомлення залежно від каналу
        if channel_id == first_channel_id:
            processed_message = process_first_channel_message(original_message)
        elif channel_id == second_channel_id:
            processed_message = process_second_channel_message(original_message)
            if processed_message is None:
                print(f"⏩ Ігнорую шорт без стопа з {channel_name}")
                return
        else:
            processed_message = original_message

        # Додаткова обробка (фіксації / стоп в БУ)
        trade_update = process_trade_updates(original_message, channel_id)
        if trade_update:
            processed_message += f"\n\n{trade_update}"

        # Формування фінального повідомлення
        final_message = f"📡 {channel_name} | {timestamp}\n\n{processed_message}"

        # Виводимо у консоль
        print(f"\nОтримано з {channel_name}:\n{final_message}")

        # Надсилаємо на другий акаунт
        await client.send_message(second_user_id, final_message)

    except Exception as e:
        print(f"❌ Помилка в обробці повідомлення: {e}")
# === Запуск бота ===
async def main():
    print("✅ Підключення до Telegram...")
    await client.start()  # при першому запуску спитає номер і код
    print("🚀 Бот запущений! Слухаю канали...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())