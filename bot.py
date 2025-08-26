import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# -------------------------
# تحميل الإعدادات
# -------------------------
with open("config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
API_KEY = config["api_key"]
ADMIN_ID = config["admin_id"]
API_URL = config.get("api_url", "https://kd1s.com/api/v2")

# الخدمات: service_id : [اسم الخدمة, نقاط لكل 1000 وحدة]
SERVICES = {
    15454: ["لايكات تيك توك سريعه 👍😂", 150],
    13378: ["مشاهدات تيك توك(مليون) 💁😂", 150],
    12316: ["لايكات انستا جديده ❗️😂", 150],
    13723: ["مشاهدات ريلز انستا(مليون) ▶️😂", 150]
}

# -------------------------
# تخزين المستخدمين ونقاطهم
# -------------------------
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f, ensure_ascii=False)

# -------------------------
# أمر /start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in users:
        # إضافة المستخدم لأول مرة مع 25 نقطة
        users[user_id] = {
            "name": user.full_name,
            "username": user.username if user.username else "",
            "points": 25,
            "joined": True
        }
        save_users()

        # إشعار للمدير
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"😂👤 مستخدم جديد:\n• الاسم: {user.full_name}\n• معرف: @{user.username if user.username else 'لا يوجد'}\n• نقاطه😂: 25"
        )

    # لوحة الأزرار
    keyboard = [
        [InlineKeyboardButton("🛒 الخدمات", callback_data='services')],
        [InlineKeyboardButton("🎁 جمع النقاط", callback_data='collect')],
        [InlineKeyboardButton("📊😂 حسابك", callback_data='account')],
        [InlineKeyboardButton("⚙️😂 لوحة التحكم (Admin)", callback_data='admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"أهلاً {user.full_name} 👋\nاخترالي يعجبـك :",
        reply_markup=reply_markup
    )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == 'services':
        keyboard = []
        for sid, info in SERVICES.items():
            keyboard.append([InlineKeyboardButton(f"{info[0]} ({info[1]} نقطة لكل 1000)", callback_data=f"service_{sid}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("😒اختر الخدمة:", reply_markup=reply_markup)

    elif query.data.startswith("service_"):
        sid = int(query.data.split("_")[1])
        service = SERVICES.get(sid)
        if service:
            await query.message.reply_text(f"✅😂 اخترت خدمة: {service[0]}\nيتم احتساب {service[1]} نقطة لكل 1000 وحدة.")

    elif query.data == 'collect':
        keyboard = [
            [InlineKeyboardButton("📢😂 الاشتراك بالقناة (75 نقطة)", callback_data='sub_channel')],
            [InlineKeyboardButton("👍🔗 مشاركة رابط البوت (80 نقطة لكل مستخدم)", callback_data='share_bot')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("💁اختر طريقة جمع النقاط:", reply_markup=reply_markup)

    elif query.data == 'sub_channel':
        await query.message.reply_text("✅😑 تحقق من الاشتراك بالقناة لتستلم 75 نقطة.")
        users[user_id]['points'] += 75
        save_users()
        await query.message.reply_text(f"💰😂 تم إضافة 75 نقطة! مجموع نقاطك: {users[user_id]['points']}")

    elif query.data == 'share_bot':
        await query.message.reply_text(f"🔗 شارك هذا الرابط: https://t.me/inirbot\nلكل مستخدم ينضم من الرابط: 80 نقطة.")
        # النقاط ستضاف عند دخول مستخدم جديد عبر الرابط (ملاحظة: تحتاج لتتبع الدعوات لاحقاً)

    elif query.data == 'account':
        pts = users[user_id]['points']
        await query.message.reply_text(f"📊 حسابك:\n• الاسم🩵: {users[user_id]['name']}\n• معرف🆔: @{users[user_id]['username']}\n• 😂نقاطك: {pts}")

    elif query.data == 'admin' and user_id == str(ADMIN_ID):
        keyboard = [
            [InlineKeyboardButton("😎📦 إضافة خدمة جديدة", callback_data='add_service')],
            [InlineKeyboardButton("💰😂 إضافة/خصم نقاط", callback_data='modify_points')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("😂لوحة تحكم المدير:", reply_markup=reply_markup)

# -------------------------
# استقبال الرسائل العامة
# -------------------------
async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❗ استخدم الأزرار.")

# -------------------------
# تشغيل البوت
# -------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler))

app.run_polling()
