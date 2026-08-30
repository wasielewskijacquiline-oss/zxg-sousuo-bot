import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram Bot Token
TOKEN = "8632208346:AAGdvE-NC1GqeP5c8rAFbhIIopCZcimOLqk"

# 1. 专为通过 Render 端口健康检查准备的 HTTP 服务
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

# 2. Telegram 机器人指令与消息处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！直接发送资源名称（如：流浪地球），我来为你搜索资源。")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text.strip()
    encoded_keyword = urllib.parse.quote(keyword)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    api_url = f"https://api.pansearch.me/search?q={encoded_keyword}"

    # 尝试直连第三方 API 抓取
    try:
        res = requests.get(api_url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get("data", [])
            if results:
                msg = f"🔍 **为您找到【{keyword}】的相关资源：**\n\n"
                for item in results[:5]:
                    title = item.get('title') or item.get('name') or "未知资源"
                    link = item.get('link') or item.get('url') or "无链接"
                    msg += f"📌 **{title}**\n🔗 {link}\n\n"
                await update.message.reply_text(msg, parse_mode="Markdown")
                return
    except Exception as e:
        print(f"[API Request Failed]: {e}")

    # 若 API 被 Cloudflare 拦截或无结果，自动返回备用网页搜索通道
    search_pan = f"https://www.pansearch.me/search?q={encoded_keyword}"
    search_quark = f"https://pan.quark.cn/s/{encoded_keyword}"
    
    fallback_msg = (
        f"🔍 **已为您生成【{keyword}】的搜素通道：**\n\n"
        f"🔗 [点击此处打开 PanSearch 搜索结果]({search_pan})\n"
        f"🔗 [点击此处打开 夸克网盘 搜索通道]({search_quark})\n\n"
        f"💡 *提示：直接点击上方蓝字链接即可获取最新资源* "
    )
    
    await update.message.reply_text(
        fallback_msg, 
        parse_mode="Markdown", 
        disable_web_page_preview=True
    )

if __name__ == "__main__":
    # 3. 优先在后台启动保活端口服务
    def run_dummy_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()

    threading.Thread(target=run_dummy_server, daemon=True).start()

    # 4. 配置并运行 Telegram 机器人
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    
    app.run_polling(close_loop=False)
