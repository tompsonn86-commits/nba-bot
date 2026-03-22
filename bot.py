"""
NBA Betting Telegram Bot
Отслеживает матчи НБА, считает статистику, присылает рекомендации
"""

import os, json, asyncio, logging
from datetime import datetime, timezone
import httpx
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

# ── конфиг из переменных окружения ──────────────────────────
TG_TOKEN   = os.environ['TG_TOKEN']
ODDS_KEY   = os.environ['ODDS_KEY']
CHAT_ID    = os.environ.get('CHAT_ID', '')   # заполним после первого /start

# ── исторические данные ──────────────────────────────────────
STATA = {"189.5":{"win":0,"lose":1,"pct":0},"187.5":{"win":0,"lose":1,"pct":0},"194.5":{"win":0,"lose":3,"pct":0},"195.5":{"win":2,"lose":0,"pct":1},"197.5":{"win":1,"lose":0,"pct":1},"199.5":{"win":3,"lose":1,"pct":0.75},"200.5":{"win":1,"lose":1,"pct":0.5},"201.5":{"win":0,"lose":3,"pct":0},"202.5":{"win":0,"lose":2,"pct":0},"203.5":{"win":1,"lose":1,"pct":0.5},"204.5":{"win":1,"lose":2,"pct":0.3333},"205.5":{"win":2,"lose":2,"pct":0.5},"206.5":{"win":2,"lose":0,"pct":1},"207.5":{"win":1,"lose":1,"pct":0.5},"208.5":{"win":4,"lose":4,"pct":0.5},"209.5":{"win":3,"lose":1,"pct":0.75},"210.5":{"win":4,"lose":2,"pct":0.6667},"211.5":{"win":1,"lose":5,"pct":0.1667},"212.5":{"win":5,"lose":2,"pct":0.7143},"213.5":{"win":5,"lose":1,"pct":0.8333},"214.5":{"win":1,"lose":4,"pct":0.2},"215.5":{"win":6,"lose":0,"pct":1},"216.5":{"win":8,"lose":6,"pct":0.5714},"217.5":{"win":10,"lose":2,"pct":0.8333},"218.5":{"win":7,"lose":3,"pct":0.7},"219.5":{"win":8,"lose":3,"pct":0.7273},"220.5":{"win":8,"lose":3,"pct":0.7273},"221.5":{"win":11,"lose":11,"pct":0.5},"222.5":{"win":7,"lose":3,"pct":0.7},"223.5":{"win":9,"lose":6,"pct":0.6},"224.5":{"win":6,"lose":3,"pct":0.6667},"225.5":{"win":10,"lose":3,"pct":0.7692},"226.5":{"win":4,"lose":4,"pct":0.5},"227.5":{"win":12,"lose":8,"pct":0.6},"228.5":{"win":7,"lose":6,"pct":0.5385},"229.5":{"win":3,"lose":12,"pct":0.2},"230.5":{"win":5,"lose":11,"pct":0.3125},"231.5":{"win":9,"lose":6,"pct":0.6},"232.5":{"win":5,"lose":9,"pct":0.3571},"233.5":{"win":6,"lose":7,"pct":0.4615},"234.5":{"win":8,"lose":5,"pct":0.6154},"235.5":{"win":10,"lose":5,"pct":0.6667},"236.5":{"win":6,"lose":6,"pct":0.5},"237.5":{"win":5,"lose":7,"pct":0.4167},"238.5":{"win":8,"lose":4,"pct":0.6667},"239.5":{"win":6,"lose":2,"pct":0.75},"240.5":{"win":5,"lose":3,"pct":0.625},"241.5":{"win":5,"lose":9,"pct":0.3571},"242.5":{"win":4,"lose":6,"pct":0.4},"243.5":{"win":8,"lose":5,"pct":0.6154},"244.5":{"win":4,"lose":5,"pct":0.4444},"245.5":{"win":2,"lose":2,"pct":0.5},"246.5":{"win":4,"lose":4,"pct":0.5},"247.5":{"win":3,"lose":1,"pct":0.75},"248.5":{"win":2,"lose":4,"pct":0.3333},"249.5":{"win":2,"lose":0,"pct":1},"250.5":{"win":1,"lose":2,"pct":0.3333},"251.5":{"win":1,"lose":2,"pct":0.3333},"252.5":{"win":3,"lose":2,"pct":0.6},"253.5":{"win":4,"lose":4,"pct":0.5},"254.5":{"win":2,"lose":5,"pct":0.2857},"255.5":{"win":3,"lose":2,"pct":0.6},"256.5":{"win":2,"lose":0,"pct":1},"257.5":{"win":4,"lose":1,"pct":0.8},"259.5":{"win":0,"lose":1,"pct":0},"260.5":{"win":1,"lose":0,"pct":1},"268.5":{"win":2,"lose":0,"pct":1},"269.5":{"win":0,"lose":1,"pct":0}}
DELTA = {"0.5":{"win":9,"lose":11,"pct":0.45},"1.5":{"win":9,"lose":9,"pct":0.5},"2.5":{"win":9,"lose":4,"pct":0.6923},"3.5":{"win":7,"lose":9,"pct":0.4375},"4.5":{"win":5,"lose":7,"pct":0.4167},"5.5":{"win":9,"lose":5,"pct":0.6429},"6.5":{"win":12,"lose":3,"pct":0.8},"7.5":{"win":12,"lose":4,"pct":0.75},"8.5":{"win":6,"lose":5,"pct":0.5455},"9.5":{"win":5,"lose":6,"pct":0.4545},"10.5":{"win":2,"lose":5,"pct":0.2857},"11.5":{"win":6,"lose":4,"pct":0.6},"12.5":{"win":4,"lose":6,"pct":0.4},"13.5":{"win":8,"lose":3,"pct":0.7273},"14.5":{"win":6,"lose":6,"pct":0.5},"15.5":{"win":5,"lose":4,"pct":0.5556},"16.5":{"win":2,"lose":3,"pct":0.4},"17.5":{"win":1,"lose":2,"pct":0.3333},"18.5":{"win":2,"lose":1,"pct":0.6667},"19.5":{"win":2,"lose":2,"pct":0.5},"20.5":{"win":4,"lose":0,"pct":1},"21.5":{"win":3,"lose":4,"pct":0.4286},"22.5":{"win":3,"lose":0,"pct":1},"23.5":{"win":2,"lose":0,"pct":1},"24.5":{"win":1,"lose":0,"pct":1},"26.5":{"win":0,"lose":2,"pct":0},"28.5":{"win":0,"lose":1,"pct":0},"29.5":{"win":1,"lose":0,"pct":1},"31.5":{"win":2,"lose":1,"pct":0.6667},"33.5":{"win":1,"lose":0,"pct":1},"34.5":{"win":0,"lose":1,"pct":0},"45.5":{"win":1,"lose":0,"pct":1},"-0.5":{"win":12,"lose":14,"pct":0.4615},"-1.5":{"win":8,"lose":6,"pct":0.5714},"-2.5":{"win":8,"lose":5,"pct":0.6154},"-3.5":{"win":8,"lose":3,"pct":0.7273},"-4.5":{"win":7,"lose":10,"pct":0.4118},"-5.5":{"win":7,"lose":8,"pct":0.4667},"-6.5":{"win":7,"lose":8,"pct":0.4667},"-7.5":{"win":4,"lose":7,"pct":0.3636},"-8.5":{"win":11,"lose":3,"pct":0.7857},"-9.5":{"win":3,"lose":5,"pct":0.375},"-10.5":{"win":8,"lose":3,"pct":0.7273},"-11.5":{"win":5,"lose":6,"pct":0.4545},"-12.5":{"win":7,"lose":4,"pct":0.6364},"-13.5":{"win":5,"lose":2,"pct":0.7143},"-14.5":{"win":1,"lose":7,"pct":0.125},"-15.5":{"win":4,"lose":5,"pct":0.4444},"-16.5":{"win":1,"lose":1,"pct":0.5},"-17.5":{"win":3,"lose":2,"pct":0.6},"-18.5":{"win":5,"lose":2,"pct":0.7143},"-19.5":{"win":2,"lose":2,"pct":0.5},"-20.5":{"win":3,"lose":2,"pct":0.6},"-21.5":{"win":3,"lose":2,"pct":0.6},"-22.5":{"win":3,"lose":0,"pct":1},"-23.5":{"win":4,"lose":6,"pct":0.4},"-24.5":{"win":3,"lose":5,"pct":0.375},"-25.5":{"win":3,"lose":1,"pct":0.75},"-27.5":{"win":1,"lose":1,"pct":0.5},"-29.5":{"win":1,"lose":1,"pct":0.5},"-30.5":{"win":1,"lose":0,"pct":1},"-32.5":{"win":0,"lose":1,"pct":0},"-33.5":{"win":1,"lose":0,"pct":1},"-36.5":{"win":1,"lose":0,"pct":1},"-37.5":{"win":1,"lose":1,"pct":0.5}}
MIN_SAMPLE = 8

# ── состояние бота ───────────────────────────────────────────
# game_id -> {'home', 'away', 'q1h', 'q1a', 'q2h', 'q2a', 'notified', 'waiting_total'}
STATE_FILE = 'bot_state.json'
pending = {}   # game_id -> данные матча ожидающего тотал
notified = set()  # game_ids которым уже отправили уведомление

def load_state():
    global pending, notified
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
            pending = s.get('pending', {})
            notified = set(s.get('notified', []))
        except: pass

def save_state():
    with open(STATE_FILE, 'w') as f:
        json.dump({'pending': pending, 'notified': list(notified)}, f)

# ── расчёт рекомендации ──────────────────────────────────────
def analyze(half: int, total_line: float) -> dict:
    need2 = total_line - half
    delta = need2 - half
    dr = round(delta * 2) / 2

    st = STATA.get(str(total_line))
    dl = DELTA.get(str(dr))

    total_pct = st['pct'] if st else None
    delta_pct = dl['pct'] if dl else None
    total_n = (st['win'] + st['lose']) if st else 0
    delta_n = (dl['win'] + dl['lose']) if dl else 0

    low_sample = total_n < MIN_SAMPLE or delta_n < MIN_SAMPLE
    recommended = (total_pct is not None and delta_pct is not None
                   and total_pct >= 0.60 and delta_pct >= 0.60
                   and not low_sample)

    return {
        'half': half,
        'need2': need2,
        'delta': dr,
        'total_line': total_line,
        'total_pct': total_pct,
        'delta_pct': delta_pct,
        'total_n': total_n,
        'delta_n': delta_n,
        'low_sample': low_sample,
        'recommended': recommended,
    }

def format_analysis(match_name: str, r: dict) -> str:
    tp = f"{round(r['total_pct']*100)}%" if r['total_pct'] is not None else "нет данных"
    dp = f"{round(r['delta_pct']*100)}%" if r['delta_pct'] is not None else "нет данных"
    dr_str = ('+' if r['delta'] >= 0 else '') + str(r['delta'])

    if r['recommended']:
        signal = "🟢 СТАВИТЬ НА МЕНЬШЕ"
    elif r['low_sample']:
        signal = "🟡 МАЛО ДАННЫХ — осторожно"
    else:
        signal = "🔴 ПРОПУСТИТЬ"

    warn = "\n⚠️ Мало данных в базе — ненадёжно" if r['low_sample'] else ""

    return (
        f"🏀 *{match_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 Набрано в 1-й пол: *{r['half']}*\n"
        f"🎯 Тотал лайв: *{r['total_line']}*\n"
        f"➡️ Нужно во 2-й пол: *{r['need2']:.1f}*\n"
        f"📐 Дельта: *{dr_str}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"% по тоталу: *{tp}* ({r['total_n']} матчей)\n"
        f"% по разнице: *{dp}* ({r['delta_n']} матчей)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{signal}{warn}"
    )

# ── получение матчей НБА из API ─────────────────────────────
async def fetch_nba_scores() -> list:
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/scores/"
    params = {
        'apiKey': ODDS_KEY,
        'daysFrom': 1,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            if r.status_code == 200:
                return r.json()
            else:
                log.error(f"API error: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.error(f"fetch error: {e}")
    return []

def parse_halftime(game: dict):
    """
    Возвращает (q1_home, q1_away, q2_home, q2_away) если матч в перерыве,
    иначе None.
    """
    scores = game.get('scores') or []
    period = game.get('period', 0)
    completed = game.get('completed', False)

    # Ищем период halftime или конец 2-й четверти
    # the-odds-api возвращает scores как список периодов
    if not scores:
        return None

    # Матч должен быть в перерыве (period=2 и не завершён)
    # или только что закончилась 2-я четверть
    score_map = {}
    for s in scores:
        name = s.get('name', '')
        periods = s.get('periods') or []
        score_map[name] = periods

    if len(score_map) < 2:
        return None

    teams = list(score_map.keys())
    home_periods = score_map.get(game.get('home_team', ''), [])
    away_periods = score_map.get(game.get('away_team', ''), [])

    # Нужно ровно 2 периода (Q1 и Q2) — значит перерыв
    if len(home_periods) == 2 and len(away_periods) == 2 and not completed:
        try:
            q1h = int(home_periods[0].get('score', 0))
            q2h = int(home_periods[1].get('score', 0))
            q1a = int(away_periods[0].get('score', 0))
            q2a = int(away_periods[1].get('score', 0))
            return q1h, q1a, q2h, q2a
        except:
            return None
    return None

# ── фоновый мониторинг ───────────────────────────────────────
async def monitor_loop(app: Application):
    """Каждые 2 минуты проверяем матчи НБА."""
    await asyncio.sleep(10)  # дать боту стартовать
    while True:
        try:
            await check_games(app)
        except Exception as e:
            log.error(f"monitor error: {e}")
        await asyncio.sleep(120)  # каждые 2 минуты

async def check_games(app: Application):
    chat_id = CHAT_ID or os.environ.get('CHAT_ID', '')
    if not chat_id:
        return

    games = await fetch_nba_scores()
    log.info(f"Fetched {len(games)} games")

    for game in games:
        gid = game.get('id', '')
        if gid in notified:
            continue

        home = game.get('home_team', '')
        away = game.get('away_team', '')
        match_name = f"{away} — {home}"

        halftime = parse_halftime(game)
        if halftime is None:
            continue

        q1h, q1a, q2h, q2a = halftime
        half_total = q1h + q1a + q2h + q2a

        log.info(f"HALFTIME detected: {match_name}, half={half_total}")

        # Сохраняем в pending — ждём /total от пользователя
        pending[gid] = {
            'match': match_name,
            'half': half_total,
            'q1h': q1h, 'q1a': q1a, 'q2h': q2h, 'q2a': q2a,
            'time': datetime.now(timezone.utc).isoformat(),
        }
        notified.add(gid)
        save_state()

        # Отправляем уведомление
        msg = (
            f"🏀 *ПЕРЕРЫВ!*\n"
            f"*{match_name}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"1-я четверть: {q1a} — {q1h}\n"
            f"2-я четверть: {q2a} — {q2h}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 Сумма 1-й половины: *{half_total} очков*\n\n"
            f"Открой betcity, найди этот матч и введи тотал:\n"
            f"`/total {half_total} 226.5`\n"
            f"_(замени 226.5 на тотал из betcity)_"
        )
        await app.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode='Markdown'
        )

# ── команды бота ─────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    # Сохраняем chat_id в env (для Railway используем файл)
    with open('chat_id.txt', 'w') as f:
        f.write(chat_id)
    # Обновляем глобальную переменную
    global CHAT_ID
    CHAT_ID = chat_id

    await update.message.reply_text(
        "🏀 *NBA Betting Bot запущен!*\n\n"
        "Я слежу за матчами НБА.\n"
        "Когда закончится 1-я половина — пришлю уведомление.\n\n"
        "Ты вводишь тотал из betcity командой:\n"
        "`/total 226.5`\n\n"
        "Если хочешь проверить конкретный матч вручную:\n"
        "`/check 108 226.5`\n"
        "_(108 = очки 1-й половины, 226.5 = тотал)_\n\n"
        "Посмотреть активные матчи: /games",
        parse_mode='Markdown'
    )

async def cmd_total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /total 226.5  — если есть один активный матч в перерыве
    /total 108 226.5  — явно указать очки и тотал
    """
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Используй:\n`/total 226.5` — для последнего матча в перерыве\n"
            "`/total 108 226.5` — указать очки и тотал вручную",
            parse_mode='Markdown'
        )
        return

    try:
        if len(args) == 1:
            # Ищем последний pending матч
            if not pending:
                await update.message.reply_text(
                    "Нет активных матчей в перерыве.\n"
                    "Используй `/total 108 226.5` чтобы ввести вручную.",
                    parse_mode='Markdown'
                )
                return
            # Берём последний по времени
            gid = sorted(pending.keys(), key=lambda k: pending[k].get('time', ''))[-1]
            game_data = pending[gid]
            half = game_data['half']
            total_line = float(args[0])
            match_name = game_data['match']

        elif len(args) == 2:
            half = int(args[0])
            total_line = float(args[1])
            match_name = "Ручной ввод"
        else:
            raise ValueError("wrong args")

    except (ValueError, IndexError):
        await update.message.reply_text(
            "Неверный формат.\nПример: `/total 226.5` или `/total 108 226.5`",
            parse_mode='Markdown'
        )
        return

    r = analyze(half, total_line)
    msg = format_analysis(match_name, r)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/check 108 226.5 — быстрый ручной расчёт"""
    args = ctx.args
    if len(args) != 2:
        await update.message.reply_text(
            "Использование: `/check 108 226.5`\n"
            "108 — очки 1-й половины, 226.5 — тотал",
            parse_mode='Markdown'
        )
        return
    try:
        half = int(args[0])
        total_line = float(args[1])
    except ValueError:
        await update.message.reply_text("Ошибка: введи числа. Пример: `/check 108 226.5`", parse_mode='Markdown')
        return

    r = analyze(half, total_line)
    msg = format_analysis("Ручной расчёт", r)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_games(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/games — показать матчи в перерыве"""
    games = await fetch_nba_scores()
    halftime_games = []
    for g in games:
        ht = parse_halftime(g)
        if ht:
            q1h, q1a, q2h, q2a = ht
            half = q1h + q1a + q2h + q2a
            halftime_games.append(
                f"🏀 {g.get('away_team')} — {g.get('home_team')}\n"
                f"   1-я пол: *{half}* очков\n"
                f"   Введи: `/total {half} XXX.X`"
            )

    if not halftime_games:
        # Показываем все активные
        active = [g for g in games if not g.get('completed')]
        if active:
            lines = []
            for g in active[:5]:
                scores = g.get('scores') or []
                home_sc = away_sc = '?'
                for s in scores:
                    if s['name'] == g['home_team']:
                        home_sc = s.get('score', '?')
                    elif s['name'] == g['away_team']:
                        away_sc = s.get('score', '?')
                lines.append(f"• {g.get('away_team')} {away_sc} — {home_sc} {g.get('home_team')}")
            await update.message.reply_text(
                "Активные матчи НБА (не в перерыве):\n" + "\n".join(lines),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("Сейчас нет активных матчей НБА.")
        return

    await update.message.reply_text(
        "⏸ *Матчи в перерыве:*\n\n" + "\n\n".join(halftime_games),
        parse_mode='Markdown'
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/status — состояние бота"""
    games = await fetch_nba_scores()
    active = len([g for g in games if not g.get('completed')])
    await update.message.reply_text(
        f"✅ Бот работает\n"
        f"🏀 Активных матчей НБА: {active}\n"
        f"⏸ Ожидают тотала: {len(pending)}\n"
        f"📊 Уведомлено сегодня: {len(notified)}\n"
        f"🔄 Проверка каждые 2 минуты"
    )

# ── запуск ───────────────────────────────────────────────────
def main():
    load_state()

    # Загружаем chat_id если сохранён
    global CHAT_ID
    if not CHAT_ID and os.path.exists('chat_id.txt'):
        with open('chat_id.txt') as f:
            CHAT_ID = f.read().strip()

    app = Application.builder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('total', cmd_total))
    app.add_handler(CommandHandler('check', cmd_check))
    app.add_handler(CommandHandler('games', cmd_games))
    app.add_handler(CommandHandler('status', cmd_status))

    # Запускаем фоновый мониторинг
    async def post_init(app):
        asyncio.create_task(monitor_loop(app))

    app.post_init = post_init

    log.info("Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
