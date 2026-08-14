import telebot
from telebot import types
import html
import time
import os
from collections import defaultdict

# Railway uses Environment Variables, so we read the token from there
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8351461662:AAGBql9Z-scysh-ofC_tw4-UhZO_RfQgHJs")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

batches = defaultdict(dict)

def to_normal_mono(text):
    if not text:
        return ""
    safe_text = html.escape(text)
    return f"<code>{safe_text}</code>"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "👋 <b>Welcome to Mono Caption Bot!</b>\n\n"
        "1️⃣ Forward/send one or multiple videos.\n"
        "2️⃣ Tap the button to process the batch.\n"
        "3️⃣ Get them back instantly with <code>monospace</code> captions."
    )

@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id

    if "videos" not in batches[chat_id]:
        batches[chat_id]["videos"] = []
        
    batches[chat_id]["videos"].append({
        "message_id": message.message_id,
        "caption": message.caption or "",
    })

    count = len(batches[chat_id]["videos"])
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"🚀 Process Batch ({count})", callback_data="process_batch"))

    if "msg_id" in batches[chat_id]:
        try:
            bot.edit_message_text(
                text=f"📦 <b>Batch Queue</b>\n━━━━━━━━━━━━━\n✅ Videos in queue: <b>{count}</b>\n\nSend more or tap below to start.",
                chat_id=chat_id,
                message_id=batches[chat_id]["msg_id"],
                reply_markup=kb
            )
            return
        except:
            pass

    msg = bot.reply_to(
        message,
        f"📦 <b>Batch Queue</b>\n━━━━━━━━━━━━━\n✅ Videos in queue: <b>{count}</b>\n\nSend more or tap below to start.",
        reply_markup=kb
    )
    batches[chat_id]["msg_id"] = msg.message_id

@bot.callback_query_handler(func=lambda c: c.data == "process_batch")
def process_batch_callback(call):
    chat_id = call.message.chat.id
    session = batches.get(chat_id)

    if not session or not session.get("videos"):
        bot.answer_callback_query(call.id, "⚠️ No videos found.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🚀 Processing...")
    
    videos = session["videos"]
    total = len(videos)
    start_time = time.time()
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⏳ Processing...", callback_data="ignore"))
    bot.edit_message_text(
        text=f"⚙️ <b>Processing Batch...</b>\n━━━━━━━━━━━━━\n📤 Uploading <b>{total}</b> videos...",
        chat_id=chat_id,
        message_id=session["msg_id"],
        reply_markup=kb
    )

    success_count = 0
    
    for i, info in enumerate(videos, 1):
        try:
            mono_caption = to_normal_mono(info["caption"])
            bot.copy_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=info["message_id"],
                caption=mono_caption if mono_caption else None
            )
            success_count += 1
        except Exception as e:
            bot.send_message(chat_id, f"❌ <b>Error on video {i}:</b>\n<code>{e}</code>")

    elapsed_time = round(time.time() - start_time, 2)
    kb_done = types.InlineKeyboardMarkup()
    kb_done.add(types.InlineKeyboardButton("✅ Done", callback_data="ignore"))
    
    bot.edit_message_text(
        text=f"🎉 <b>Batch Complete!</b>\n━━━━━━━━━━━━━\n"
             f"✅ Processed: <b>{success_count}/{total}</b>\n"
             f"⏱️ Time: <b>{elapsed_time}s</b>\n\n"
             f"Send more videos to start a new batch!",
        chat_id=chat_id,
        message_id=session["msg_id"],
        reply_markup=kb_done
    )

    del batches[chat_id]

print("Bot is running...")
bot.infinity_polling()
