import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram Bot Token
TOKEN = "8632208346:AAEgjua5CSyMbs1s9CetcZM0hnNZBtD3590"

# 1. 专为通过 Render 端口健康检查准备的简易 HTTP 服务
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 屏蔽健康检查日志，保持控制台干净

# 2. Telegram 机器人指令与消息处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！直接发送关键词（如：流浪地球），我来为你找资源。")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text
    api_url = f"https://api.pansearch.me/search?q={keyword}"

    try:
        res = requests.get(api_url, timeout=10).json()
        results = res.get("data", [])
        if not results:
            await update.message.reply_text("未找到相关资源，换个关键词试试吧。")
            return

        msg = "🔍 **找到以下资源：**\n\n"
        for item in results[:5]:
            msg += f"📌 **{item.get('title')}**\n🔗 {item.get('link')}\n\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("搜索服务繁忙，请稍后再试。")

if __name__ == "__main__":
    # 3. 优先在后台启动保活端口服务（绑定 Render 要求的 PORT）
    def run_dummy_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()

    threading.Thread(target=run_dummy_server, daemon=True).start()

    # 4. 配置并运行 Telegram 机器人（阻塞程序，必须放最后）
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    
    app.run_polling()
    app.run_polling()
