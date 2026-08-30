import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 填入你从 BotFather 拿到的 Token
TOKEN = "8632208346:AAEgjua5CSyMbs1s9CetcZM0hnNZBtD3590"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！直接发送关键词（如：流浪地球），我来为你找资源。")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text
    # 此处调用开源盘搜/网盘搜索 API（示例逻辑）
    api_url = f"https://api.pansearch.me/search?q={keyword}" 
    
    try:
        res = requests.get(api_url, timeout=10).json()
        results = res.get("data", [])
        if not results:
            await update.message.reply_text("未找到相关资源，换个关键词试试吧。")
            return
            
        msg = "🔍 **找到以下资源：**\n\n"
        for item in results[:5]:  # 取前5条展示
            msg += f"📌 **{item.get('title')}**\n🔗 {item.get('link')}\n\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("搜索服务繁忙，请稍后再试。")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.run_polling()
# 专门应对 Render Web Service 的端口保活
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
