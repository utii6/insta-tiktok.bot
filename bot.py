# bot.py
import json
import requests
import logging
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# تحميل الإعدادات
# -------------------------
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
API_KEY = config["api_key"]
ADMIN_ID = config.get("admin_id")
API_URL = config.get("api_url", "https://kd1s.com/api/v2")

# -------------------------
# الخدمات
# -------------------------
SERVICES = [
    {"id": 15454, "title": "لايكات تيك توك سريعه 👍😂"},
    {"id": 13378, "title": "مشاهدات تيك توك(مليون) 💁😂"},
    {"id": 12316, "title": "لايكات انستا جديده ❗️😂"},
    {"id": 13723, "title": "مشاهدات ريلز انستا(مليون) ▶️😂"},
]

# -------------------------
# ملف المستخدمين
# -------------------------
USERS_FILE = "users.json"
try:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
        if not isinstance(users, list):
            users = []
except:
    users = []

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# -------------------------
# Telegram Application
# -------------------------
app_telegram = Application.builder().token(BOT_TOKEN).build()

def services_keyboard():
    rows = [[InlineKeyboardButton(s["title"], callback_data=f"svc_{s['id']}")] for s in SERVICES]
    rows.append([InlineKeyboardButton("❌😑 إلغاء العملية", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_time = False
    if user.id not in users:
        users.append(user.id)
        save_users()
        first_time = True
        # إشعار للمدير
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"دخل مستخدم جديد 👤\nالاسم: {user.full_name}\nالايدي: {user.id}"
                )
            except:
                pass
    
    if first_time:
        # رسالة الترحيب الشخصية
        await update.message.reply_text(
            f"هلا حبيبي {user.username if user.username else user.full_name} 🤗\nالبوت بوتك ويقدر يستخدمه بأي وقت!"
        )
    
    # عرض أزرار الخدمات
    await update.message.reply_text(
        "اختر خدمة من الأزرار التالية:",
        reply_markup=services_keyboard()
    )

async def services_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اختر خدمة من القائمة 😂👇", reply_markup=services_keyboard())

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("تم إلغاء العملية 💔✅", reply_markup=services_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("تم إلغاء العملية ✅💔", reply_markup=services_keyboard())
        return

    if data.startswith("svc_"):
        service_id = int(data.split("_", 1)[1])
        context.user_data["service_id"] = service_id
        context.user_data["flow"] = "await_link"
        await query.edit_message_text("😂✅ أرسل رابط المنشور 🔗")

async def text_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("flow")
    if flow == "await_link":
        context.user_data["link"] = update.message.text.strip()
        context.user_data["flow"] = "await_qty"
        await update.message.reply_text("تمام ✅😂\nأرسل الكمية المطلوبة (رقم فقط).")
    elif flow == "await_qty":
        if not update.message.text.isdigit():
            await update.message.reply_text("❌🦾 أرسل رقم صحيح.")
            return
        qty = int(update.message.text)
        service_id = context.user_data.get("service_id")
        link = context.user_data.get("link")
        try:
            r = requests.post(API_URL, data={
                "key": API_KEY,
                "action": "add",
                "service": service_id,
                "link": link,
                "quantity": qty
            }).json()
            if "order" in r:
                await update.message.reply_text(f"✅😂 تم تنفيذ الطلب!\nرقم الطلب: {r['order']}")
            else:
                await update.message.reply_text(f"❌😑 فشل الطلب.\n{r}")
        except Exception as e:
            await update.message.reply_text(f"❌❗️ خطأ: {e}")
        context.user_data.clear()

# -------------------------
# Handlers
# -------------------------
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(CommandHandler("services", services_cmd))
app_telegram.add_handler(CommandHandler("cancel", cancel_cmd))
app_telegram.add_handler(CallbackQueryHandler(button_handler))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_flow))

# -------------------------
# FastAPI Webhook
# -------------------------
fastapi_app = FastAPI()

# -------------------------
# FastAPI Webhook
# -------------------------
fastapi_app = FastAPI()

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://insta-tiktok-bot.onrender.com{WEBHOOK_PATH}"

@fastapi_app.on_event("startup")
async def startup():
    # ضبط الـ Webhook عند تشغيل البوت
    await app_telegram.bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

@fastapi_app.post(WEBHOOK_PATH)
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_telegram.bot)
    await app_telegram.process_update(update)
    return {"ok": True}
