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
    
    # 加入浏览器请求头伪装（防止 API 防爬虫拦截）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.pansearch.me/"
    }

    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        print(f"[Log] API 状态码: {res.status_code}")
        
        if res.status_code != 200:
            print(f"[Error] API 拦截或报错: {res.text[:200]}")
            await update.message.reply_text("搜索服务响应异常，请换个关键词试试。")
            return

        data = res.json()
        results = data.get("data", [])
        
        if not results:
            await update.message.reply_text("未找到相关资源，换个关键词试试吧。")
            return

        msg = "🔍 **找到以下资源：**\n\n"
        for item in results[:5]:
            title = item.get('title') or item.get('name') or "未知资源"
            link = item.get('link') or item.get('url') or "无链接"
            msg += f"📌 **{title}**\n🔗 {link}\n\n"
            
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        print(f"[Exception] 详细报错原因: {e}")
        await update.message.reply_text("搜索服务繁忙，请稍后再试。")

if __name__ == "__main__":
    # 3. 优先在后台启动保活端口服务
    def run_dummy_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()

    threading.Thread(target=run_dummy_server, daemon=True).start()

    # 4. 配置并运行 Telegram 机器人（阻塞程序，必须放最后）
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    
    # 加入 close_loop=False 参数，防止异常退出时引发事件循环崩溃
    app.run_polling(close_loop=False)
