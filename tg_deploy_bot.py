#!/usr/bin/env python3
"""
Telegram Bot for Remote Kaggle Deploy
Run on your VPS/phone to deploy via Telegram commands.

Setup:
1. Create bot via @BotFather → get BOT_TOKEN
2. Get your chat_id: @userinfobot
3. Set env: BOT_TOKEN, ADMIN_CHAT_ID
4. Run: python3 tg_deploy_bot.py

Commands:
/deploy tahsine <model>     - Deploy tahsine pipeline
/deploy bugtrace            - Deploy bugtrace
/deploy horde               - Start AI Horde worker
/status                     - Check running endpoints
/stop                       - Stop all
/help                       - Show help
"""

import os, asyncio, subprocess, json, signal
from pathlib import Path

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError:
    print("pip install python-telegram-bot")
    exit(1)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))

if not BOT_TOKEN or not ADMIN_CHAT_ID:
    print("Set BOT_TOKEN and ADMIN_CHAT_ID env vars")
    exit(1)

SCRIPTS_DIR = Path(__file__).parent
RUNNING = {}

async def run_script(update: Update, name: str, args: list):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized")
        return

    script = SCRIPTS_DIR / f"kaggle_{name}_setup.py"
    if not script.exists():
        await update.message.reply_text(f"❌ Script not found: {script}")
        return

    await update.message.reply_text(f"🚀 Starting {name} deploy...")
    
    proc = await asyncio.create_subprocess_exec(
        "python3", str(script), *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    RUNNING[name] = proc
    
    # Stream output
    async def stream_output():
        async for line in proc.stdout:
            if line.strip():
                await update.message.reply_text(f"`{line.decode().strip()}`", parse_mode="Markdown")
        async for line in proc.stderr:
            if line.strip():
                await update.message.reply_text(f"⚠️ `{line.decode().strip()}`", parse_mode="Markdown")
        await proc.wait()
        RUNNING.pop(name, None)
        await update.message.reply_text(f"✅ {name} finished (exit {proc.returncode})")
    
    asyncio.create_task(stream_output())

async def deploy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /deploy <tahsine|bugtrace|horde> [model]")
        return
    await run_script(update, context.args[0], context.args[1:])

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    if not RUNNING:
        await update.message.reply_text("No running deploys")
    else:
        msg = "🔄 Running:\n" + "\n".join(f"  • {k} (pid {v.pid})" for k, v in RUNNING.items())
        await update.message.reply_text(msg)

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    for name, proc in RUNNING.items():
        proc.terminate()
    RUNNING.clear()
    await update.message.reply_text("🛑 All stopped")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
🤖 **Kaggle Deploy Bot**

**Commands:**
/deploy tahsine [model]  - Full llama.cpp pipeline
/deploy bugtrace         - Single-cell BugTraceAI
/deploy horde            - AI Horde worker
/status                  - Show running
/stop                    - Stop all
/help                    - This help

**Models for tahsine:**
- qwen3-27b (default)
- dolphin-24b
- gemma-31b
""", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("deploy", deploy_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))
    
    print("Bot running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()