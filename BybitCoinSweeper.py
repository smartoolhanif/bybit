import os
import pyfiglet
from colorama import Fore, Style, init
import time, json, requests, hmac, hashlib, random, pytz, math
from urllib.parse import urlparse, parse_qs
from user_agent import generate_user_agent
from datetime import datetime
from time import sleep
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

user_agent = generate_user_agent('android')
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'authorization': 'Bearer ',
    'cache-control': 'no-cache',
    'origin': 'https://bybitcoinsweeper.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://bybitcoinsweeper.com/',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Android WebView";v="128"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'tl-init-data': '',
    'user-agent': user_agent,
    'x-requested-with': 'org.telegram.messenger',
}
init(autoreset=True)

def generate_hash(key, message):
    hmac_obj = hmac.new(key.encode(), message.encode(), hashlib.sha256)
    return hmac_obj.hexdigest()

def value(input_str):
    return sum(ord(char) for char in input_str) / 1e5

def calc(i, s, a, o, d, g):
    st = (10 * i + max(0, 1200 - 10 * s) + 2000) * (1 + o / a) / 10
    return math.floor(st) + value(g)

def verify(session):
    parsed_url = urlparse(session)
    query_params = parse_qs(parsed_url.fragment)
    tgWebAppData = query_params.get('tgWebAppData', [None])[0]
    headers['rawdata'] = tgWebAppData
    headers['tl-init-data'] = tgWebAppData
    response = requests.post("https://api.bybitcoinsweeper.com/api/auth/login", json={"initData": tgWebAppData}, headers=headers)
    return response.json()

def play_sweeper(url, game_time):
    data = verify(url)
    headers['Authorization'] = f"Bearer {data['accessToken']}"
    playgame = requests.post('https://api.bybitcoinsweeper.com/api/games/start', headers=headers).json()
    userdata = requests.get("https://api.bybitcoinsweeper.com/api/users/me", headers=headers).json()
    
    gameid = playgame["id"]
    rewarddata = playgame["rewards"]
    started_at = playgame["createdAt"]
    unix_time_started = datetime.strptime(started_at, '%Y-%m-%dT%H:%M:%S.%fZ')
    unix_time_started = unix_time_started.replace(tzinfo=pytz.UTC)
    starttime = int(unix_time_started.timestamp() * 1000)
    i = f"{userdata['id']}v$2f1"
    first = f"{i}-{gameid}-{starttime}"
    last = f"{game_time}-{gameid}"
    score = calc(45, game_time, 54, 9, True, gameid)
    sleep(game_time)
    game_data = {
        "bagCoins": rewarddata["bagCoins"],
        "bits": rewarddata["bits"],
        "gifts": rewarddata["gifts"],
        "gameId": gameid,
        'gameTime': game_time,
        "h": generate_hash(first, last),
        'score': float(score)
    }
    e = requests.post('https://api.bybitcoinsweeper.com/api/games/win', json=game_data, headers=headers)
    return (e.status_code, score)

def create_gradient_banner(text):
    banner = pyfiglet.figlet_format(text).splitlines()
    colors = [Fore.GREEN + Style.BRIGHT, Fore.YELLOW + Style.BRIGHT, Fore.RED + Style.BRIGHT]
    total_lines = len(banner)
    section_size = total_lines // len(colors)
    for i, line in enumerate(banner):
        if i < section_size:
            print(colors[0] + line)  # Green
        elif i < section_size * 2:
            print(colors[1] + line)  # Yellow
        else:
            print(colors[2] + line)  # Red

# Telegram Bot Handlers
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Please enter your BybitCoinSweeper session link using /session <link>")

def session(update: Update, context: CallbackContext) -> None:
    session_link = " ".join(context.args)
    context.user_data['session_link'] = session_link
    update.message.reply_text(f"Session link received: {session_link}\nNow enter the game time using /gametime <seconds>")

def gametime(update: Update, context: CallbackContext) -> None:
    try:
        game_time = int(context.args[0])
        session_link = context.user_data.get('session_link')
        if session_link:
            update.message.reply_text(f"Starting game with session link: {session_link} and game time: {game_time}")
            status, score = play_sweeper(session_link, game_time)
            update.message.reply_text(f"Game finished!\nStatus Code: {status}\nScore: {score}")
        else:
            update.message.reply_text("Session link not found. Please enter the session link first using /session <link>")
    except (IndexError, ValueError):
        update.message.reply_text("Invalid game time. Please enter a valid number in seconds.")

def main():
    # Initialize the Telegram bot
    updater = Updater("6787721337:AAFi6uq3NFGFXpFvPu0JifsOTKDf8LjnzoY", use_context=True)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("session", session))
    dispatcher.add_handler(CommandHandler("gametime", gametime))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
    