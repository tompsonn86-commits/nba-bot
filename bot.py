"""
NBA Betting Telegram Bot v3
Полностью автоматический:
- Следит за матчами НБА каждые 90 секунд
- В перерыве присылает счёт → ты вводишь тотал → получаешь рекомендацию
- После матча сам определяет WIN/LOSE и обновляет базу
"""

import os, json, asyncio, logging, copy
from datetime import datetime, timezone
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

TG_TOKEN = os.environ['TG_TOKEN']
ODDS_KEY = os.environ['ODDS_KEY']
CHAT_ID  = os.environ.get('CHAT_ID', '')

BASE_STATA = {"189.5":{"win":0,"lose":1},"187.5":{"win":0,"lose":1},"194.5":{"win":0,"lose":3},"195.5":{"win":2,"lose":0},"197.5":{"win":1,"lose":0},"199.5":{"win":3,"lose":1},"200.5":{"win":1,"lose":1},"201.5":{"win":0,"lose":3},"202.5":{"win":0,"lose":2},"203.5":{"win":1,"lose":1},"204.5":{"win":1,"lose":2},"205.5":{"win":2,"lose":2},"206.5":{"win":2,"lose":0},"207.5":{"win":1,"lose":1},"208.5":{"win":4,"lose":4},"209.5":{"win":3,"lose":1},"210.5":{"win":4,"lose":2},"211.5":{"win":1,"lose":5},"212.5":{"win":5,"lose":2},"213.5":{"win":5,"lose":1},"214.5":{"win":1,"lose":4},"215.5":{"win":6,"lose":0},"216.5":{"win":8,"lose":6},"217.5":{"win":10,"lose":2},"218.5":{"win":7,"lose":3},"219.5":{"win":8,"lose":3},"220.5":{"win":8,"lose":3},"221.5":{"win":11,"lose":11},"222.5":{"win":7,"lose":3},"223.5":{"win":9,"lose":6},"224.5":{"win":6,"lose":3},"225.5":{"win":10,"lose":3},"226.5":{"win":4,"lose":4},"227.5":{"win":12,"lose":8},"228.5":{"win":7,"lose":6},"229.5":{"win":3,"lose":12},"230.5":{"win":5,"lose":11},"231.5":{"win":9,"lose":6},"232.5":{"win":5,"lose":9},"233.5":{"win":6,"lose":7},"234.5":{"win":8,"lose":5},"235.5":{"win":10,"lose":5},"236.5":{"win":6,"lose":6},"237.5":{"win":5,"lose":7},"238.5":{"win":8,"lose":4},"239.5":{"win":6,"lose":2},"240.5":{"win":5,"lose":3},"241.5":{"win":5,"lose":9},"242.5":{"win":4,"lose":6},"243.5":{"win":8,"lose":5},"244.5":{"win":4,"lose":5},"245.5":{"win":2,"lose":2},"246.5":{"win":4,"lose":4},"247.5":{"win":3,"lose":1},"248.5":{"win":2,"lose":4},"249.5":{"win":2,"lose":0},"250.5":{"win":1,"lose":2},"251.5":{"win":1,"lose":2},"252.5":{"win":3,"lose":2},"253.5":{"win":4,"lose":4},"254.5":{"win":2,"lose":5},"255.5":{"win":3,"lose":2},"256.5":{"win":2,"lose":0},"257.5":{"win":4,"lose":1},"259.5":{"win":0,"lose":1},"260.5":{"win":1,"lose":0},"268.5":{"win":2,"lose":0},"269.5":{"win":0,"lose":1}}
BASE_DELTA = {"0.5":{"win":9,"lose":11},"1.5":{"win":9,"lose":9},"2.5":{"win":9,"lose":4},"3.5":{"win":7,"lose":9},"4.5":{"win":5,"lose":7},"5.5":{"win":9,"lose":5},"6.5":{"win":12,"lose":3},"7.5":{"win":12,"lose":4},"8.5":{"win":6,"lose":5},"9.5":{"win":5,"lose":6},"10.5":{"win":2,"lose":5},"11.5":{"win":6,"lose":4},"12.5":{"win":4,"lose":6},"13.5":{"win":8,"lose":3},"14.5":{"win":6,"lose":6},"15.5":{"win":5,"lose":4},"16.5":{"win":2,"lose":3},"17.5":{"win":1,"lose":2},"18.5":{"win":2,"lose":1},"19.5":{"win":2,"lose":2},"20.5":{"win":4,"lose":0},"21.5":{"win":3,"lose":4},"22.5":{"win":3,"lose":0},"23.5":{"win":2,"lose":0},"24.5":{"win":1,"lose":0},"26.5":{"win":0,"lose":2},"28.5":{"win":0,"lose":1},"29.5":{"win":1,"lose":0},"31.5":{"win":2,"lose":1},"33.5":{"win":1,"lose":0},"34.5":{"win":0,"lose":1},"45.5":{"win":1,"lose":0},"-0.5":{"win":12,"lose":14},"-1.5":{"win":8,"lose":6},"-2.5":{"win":8,"lose":5},"-3.5":{"win":8,"lose":3},"-4.5":{"win":7,"lose":10},"-5.5":{"win":7,"lose":8},"-6.5":{"win":7,"lose":8},"-7.5":{"win":4,"lose":7},"-8.5":{"win":11,"lose":3},"-9.5":{"win":3,"lose":5},"-10.5":{"win":8,"lose":3},"-11.5":{"win":5,"lose":6},"-12.5":{"win":7,"lose":4},"-13.5":{"win":5,"lose":2},"-14.5":{"win":1,"lose":7},"-15.5":{"win":4,"lose":5},"-16.5":{"win":1,"lose":1},"-17.5":{"win":3,"lose":2},"-18.5":{"win":5,"lose":2},"-19.5":{"win":2,"lose":2},"-20.5":{"win":3,"lose":2},"-21.5":{"win":3,"lose":2},"-22.5":{"win":3,"lose":0},"-23.5":{"win":4,"lose":6},"-24.5":{"win":3,"lose":5},"-25.5":{"win":3,"lose":1},"-27.5":{"win":1,"lose":1},"-29.5":{"win":1,"lose":1},"-30.5":{"win":1,"lose":0},"-32.5":{"win":0,"lose":1},"-33.5":{"win":1,"lose":0},"-36.5":{"win":1,"lose":0},"-37.5":{"win":1,"lose":1}}
MIN_SAMPLE = 8
BASE_COUNT = 514

STATE_FILE = 'bot_state.json'
DB_FILE    = 'matches_db.json'

pending         = {}
notified_ht     = set()
notified_result = set()
active_numbered = {}

def load_state():
    global pending, notified_ht, notified_result, active_numbered, CHAT_ID
    if os.path.exists(STATE_FILE):
        try:
            s = json.load(open(STATE_FILE))
            pending         = s.get('pending', {})
            notified_ht     = set(s.get('notified_ht', []))
            notified_result = set(s.get('notified_result', []))
            active_numbered = {int(k): v for k, v in s.get('active_numbered', {}).items()}
        except Exception as e:
            log.error(f"load_state: {e}")
    if not CHAT_ID and os.path.exists('chat_id.txt'):
        CHAT_ID = open('chat_id.txt').read().strip()

def save_state():
    with open(STATE_FILE, 'w') as f:
        json.dump({
            'pending': pending,
            'notified_ht': list(notified_ht),
            'notified_result': list(notified_result),
            'active_numbered': {str(k): v for k, v in active_numbered.items()},
        }, f, ensure_ascii=False)

def load_db():
    if os.path.exists(DB_FILE):
        try: return json.load(open(DB_FILE))
        except: pass
    return []

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def add_to_db(match_name, half, total_line, delta, result, match_total):
    db = load_db()
    db.append({
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'match': match_name, 'half': half,
        'total_line': total_line, 'delta': delta,
        'match_total': match_total, 'result': result,
    })
    save_db(db)
    return len(db)

def compute_stats():
    stata = copy.deepcopy(BASE_STATA)
    delta = copy.deepcopy(BASE_DELTA)
    for m in load_db():
        if m.get('result') not in ('WIN', 'LOSE'):
            continue
        w = m['result'] == 'WIN'
        tl = str(m.get('total_line', ''))
        d  = str(m.get('delta', ''))
        if tl:
            stata.setdefault(tl, {'win':0,'lose':0})
            stata[tl]['win' if w else 'lose'] += 1
        if d:
            delta.setdefault(d, {'win':0,'lose':0})
            delta[d]['win' if w else 'lose'] += 1
    for v in list(stata.values()) + list(delta.values()):
        ww, ll = v['win'], v['lose']
        v['pct'] = round(ww/(ww+ll), 4) if (ww+ll) > 0 else 0
    return stata, delta

def analyze(half, total_line):
    stata, dmap = compute_stats()
    need2 = total_line - half
    dr    = round((need2 - half) * 2) / 2
    st    = stata.get(str(total_line))
    dl    = dmap.get(str(dr))
    tp    = st['pct'] if st else None
    dp    = dl['pct'] if dl else None
    tn    = (st['win']+st['lose']) if st else 0
    dn    = (dl['win']+dl['lose']) if dl else 0
    low   = tn < MIN_SAMPLE or dn < MIN_SAMPLE
    rec   = tp is not None and dp is not None and tp >= 0.6 and dp >= 0.6 and not low
    return dict(half=half, need2=need2, delta=dr, total_line=total_line,
                total_pct=tp, delta_pct=dp, total_n=tn, delta_n=dn,
                low_sample=low, recommended=rec)

def fmt_rec(match_name, r):
    tp   = f"{round(r['total_pct']*100)}%" if r['total_pct'] is not None else "нет данных"
    dp   = f"{round(r['delta_pct']*100)}%" if r['delta_pct'] is not None else "нет данных"
    dstr = ('+' if r['delta'] >= 0 else '') + str(r['delta'])
    db_n = BASE_COUNT + len(load_db())
    if r['recommended']:
        signal = "🟢 СТАВИТЬ НА МЕНЬШЕ"
    elif r['low_sample']:
        signal = "🟡 МАЛО ДАННЫХ — осторожно"
    else:
        signal = "🔴 ПРОПУСТИТЬ"
    warn = "\n⚠️ Мало данных — ненадёжно" if r['low_sample'] else ""
    return (
        f"🏀 *{match_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 1-я половина: *{r['half']}* очков\n"
        f"🎯 Тотал лайв: *{r['total_line']}*\n"
        f"➡️ Нужно во 2-й: *{r['need2']:.1f}*\n"
        f"📐 Дельта: *{dstr}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"% по тоталу:  *{tp}* ({r['total_n']} матчей)\n"
        f"% по разнице: *{dp}* ({r['delta_n']} матчей)\n"
        f"📦 В базе: *{db_n}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{signal}{warn}"
    )

async def fetch_scores():
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                "https://api.the-odds-api.com/v4/sports/basketball_nba/scores/",
                params={'apiKey': ODDS_KEY, 'daysFrom': 1}
            )
            if r.status_code == 200:
                return r.json()
            log.error(f"API {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log.error(f"fetch: {e}")
    return []

def get_periods(game):
    home = game.get('home_team','')
    away = game.get('away_team','')
    sm = {}
    for s in (game.get('scores') or []):
        sm[s.get('name','')] = s.get('periods') or []
    return sm.get(home,[]), sm.get(away,[])

def is_halftime(game):
    if game.get('completed'): return False
    hp, ap = get_periods(game)
    return len(hp) == 2 and len(ap) == 2

def get_final(game):
    if not game.get('completed'): return None
    home = game.get('home_team','')
    away = game.get('away_team','')
    ht = at = None
    for s in (game.get('scores') or []):
        try: val = int(s.get('score',0))
        except: val = 0
        if s['name'] == home: ht = val
        elif s['name'] == away: at = val
    return (ht, at) if ht is not None and at is not None else None

async def monitor_loop(app):
    await asyncio.sleep(10)
    while True:
        try:
            await check_games(app)
        except Exception as e:
            log.error(f"monitor: {e}")
        await asyncio.sleep(90)

async def check_games(app):
    global active_numbered
    if not CHAT_ID: return
    games = await fetch_scores()
    new_ht = []

    for game in games:
        gid  = game.get('id','')
        home = game.get('home_team','')
        away = game.get('away_team','')
        name = f"{away} — {home}"
        hp, ap = get_periods(game)

        # ── Перерыв ──
        if is_halftime(game) and gid not in notified_ht:
            try:
                q1h=int(hp[0].get('score',0)); q2h=int(hp[1].get('score',0))
                q1a=int(ap[0].get('score',0)); q2a=int(ap[1].get('score',0))
            except: continue
            half = q1h+q1a+q2h+q2a
            pending[gid] = {'match':name,'half':half,'q1h':q1h,'q1a':q1a,'q2h':q2h,'q2a':q2a,
                            'time':datetime.now(timezone.utc).isoformat()}
            notified_ht.add(gid)
            new_ht.append(gid)
            log.info(f"HALFTIME: {name}, half={half}")

        # ── Финал: автоматический результат ──
        if game.get('completed') and gid not in notified_result:
            if gid in pending and 'total_line' in pending[gid]:
                final = get_final(game)
                if final:
                    ht_pts, at_pts = final
                    match_total = ht_pts + at_pts
                    d = pending[gid]
                    result = 'WIN' if match_total < d['total_line'] else 'LOSE'
                    db_size = add_to_db(d['match'], d['half'], d['total_line'],
                                        d['delta'], result, match_total)
                    notified_result.add(gid)
                    icon = '✅' if result == 'WIN' else '❌'
                    for num, g in list(active_numbered.items()):
                        if g == gid: del active_numbered[num]
                    del pending[gid]
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text=(
                            f"{icon} *{result} — матч завершён!*\n\n"
                            f"🏀 {d['match']}\n"
                            f"Итог: *{at_pts} — {ht_pts}* "
                            f"(тотал *{match_total}*, линия *{d['total_line']}*)\n\n"
                            f"📦 База обновлена → *{BASE_COUNT + db_size}* матчей\n"
                            f"_Следующие прогнозы точнее!_"
                        ),
                        parse_mode='Markdown'
                    )
                    log.info(f"AUTO RESULT: {name} {result}, total={match_total}")

    # Уведомление о перерыве
    if new_ht:
        active_numbered = {}
        num = 1
        for gid in sorted(pending.keys(), key=lambda k: pending[k].get('time','')):
            active_numbered[num] = gid
            num += 1

        if len(active_numbered) == 1:
            gid = list(active_numbered.values())[0]
            d = pending[gid]
            msg = (
                f"⏸ *ПЕРЕРЫВ!*\n\n"
                f"🏀 *{d['match']}*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"1-я четв: {d['q1a']} — {d['q1h']}\n"
                f"2-я четв: {d['q2a']} — {d['q2h']}\n"
                f"📊 Сумма 1-й половины: *{d['half']} очков*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Открой betcity, найди тотал матча и введи:\n"
                f"`/total 226.5`"
            )
        else:
            lines = ["⏸ *Перерыв в нескольких матчах!*\n"]
            for num, gid in active_numbered.items():
                d = pending[gid]
                lines.append(
                    f"*{num}. {d['match']}*\n"
                    f"   1-я пол: *{d['half']}* очков\n"
                    f"   ✍️ `/total {num} 226.5`"
                )
            lines.append("\n_Укажи номер матча и тотал из betcity_")
            msg = "\n\n".join(lines)

        await app.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

    save_state()

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = str(update.effective_chat.id)
    open('chat_id.txt','w').write(CHAT_ID)
    db = load_db()
    await update.message.reply_text(
        "🏀 *NBA Betting Bot v3*\n\n"
        f"📦 Матчей в базе: *{BASE_COUNT + len(db)}*\n\n"
        "*Как работает:*\n"
        "1️⃣ Конец 1-й половины → пришлю счёт\n"
        "2️⃣ Ты смотришь тотал в betcity → `/total 226.5`\n"
        "3️⃣ Получаешь рекомендацию 🟢/🔴\n"
        "4️⃣ Матч заканчивается → я сам обновляю базу ✅\n\n"
        "*Команды:*\n"
        "`/total 226.5` — ввести тотал\n"
        "`/total 2 226.5` — для матча №2\n"
        "`/check 108 226.5` — быстрый расчёт\n"
        "`/games` — активные матчи\n"
        "`/stats` — статистика базы\n"
        "`/status` — состояние бота",
        parse_mode='Markdown'
    )

async def cmd_total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Примеры:\n`/total 226.5` — один матч\n`/total 2 226.5` — матч №2",
            parse_mode='Markdown')
        return
    try:
        if len(args) == 1:
            total_line = float(args[0])
            if not active_numbered:
                await update.message.reply_text(
                    "Нет матчей в перерыве.\nДля ручного расчёта: `/check 108 226.5`",
                    parse_mode='Markdown')
                return
            num = max(active_numbered.keys())
            gid = active_numbered[num]
        elif len(args) == 2:
            num = int(args[0]); total_line = float(args[1])
            if num not in active_numbered:
                await update.message.reply_text(
                    f"Матч №{num} не найден. Доступны: {list(active_numbered.keys())}",
                    parse_mode='Markdown')
                return
            gid = active_numbered[num]
        else:
            raise ValueError()
    except (ValueError, IndexError):
        await update.message.reply_text("Формат: `/total 226.5` или `/total 2 226.5`", parse_mode='Markdown')
        return

    d = pending.get(gid, {})
    r = analyze(d.get('half', 0), total_line)
    pending[gid]['total_line']  = total_line
    pending[gid]['delta']       = r['delta']
    pending[gid]['recommended'] = r['recommended']
    save_state()
    await update.message.reply_text(fmt_rec(d.get('match','?'), r), parse_mode='Markdown')

async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if len(args) != 2:
        await update.message.reply_text("Использование: `/check 108 226.5`", parse_mode='Markdown')
        return
    try:
        r = analyze(int(args[0]), float(args[1]))
        await update.message.reply_text(fmt_rec("Ручной расчёт", r), parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("Ошибка. Пример: `/check 108 226.5`", parse_mode='Markdown')

async def cmd_games(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if active_numbered:
        lines = ["⏸ *Матчи в перерыве:*\n"]
        for num, gid in active_numbered.items():
            d = pending.get(gid, {})
            status = (f"✅ тотал {d.get('total_line')} введён" if 'total_line' in d
                      else f"⏳ жди → `/total {num} XXX.X`")
            lines.append(f"*{num}.* {d.get('match','?')}\n   1-я пол: *{d.get('half','?')}*\n   {status}")
        await update.message.reply_text("\n\n".join(lines), parse_mode='Markdown')
        return
    games = await fetch_scores()
    active = [g for g in games if not g.get('completed')]
    if active:
        lines = [f"• {g.get('away_team')} — {g.get('home_team')}" for g in active[:8]]
        await update.message.reply_text("Активные матчи:\n" + "\n".join(lines))
    else:
        await update.message.reply_text("Сейчас нет активных матчей НБА.")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    wr_m = [m for m in db if m.get('result') in ('WIN','LOSE')]
    wins = [m for m in wr_m if m['result'] == 'WIN']
    wr = round(len(wins)/len(wr_m)*100) if wr_m else 0
    last = ""
    if db:
        icons = {'WIN':'✅','LOSE':'❌'}
        last = "\n\n*Последние 5:*\n" + "\n".join(
            f"{icons.get(m.get('result',''),'❓')} {m['match']} ({m.get('result','')})"
            for m in db[-5:][::-1])
    await update.message.reply_text(
        f"📊 *Статистика базы*\n\n"
        f"📦 Базовых (Excel): *{BASE_COUNT}*\n"
        f"➕ Добавлено ботом: *{len(db)}*\n"
        f"✅ С результатом: *{len(wr_m)}*\n"
        f"📈 WR (мои матчи): *{wr}%*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🗂 Итого в базе: *{BASE_COUNT + len(db)}*" + last,
        parse_mode='Markdown'
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    games = await fetch_scores()
    active = len([g for g in games if not g.get('completed')])
    db = load_db()
    waiting = len([g for g in pending.values() if 'total_line' in g])
    await update.message.reply_text(
        f"✅ Бот работает\n"
        f"🏀 Активных матчей: {active}\n"
        f"⏸ В перерыве: {len(active_numbered)}\n"
        f"⏳ Ждут финала: {waiting}\n"
        f"📦 В базе: {BASE_COUNT + len(db)} матчей\n"
        f"🔄 Проверка каждые 90 секунд"
    )

def main():
    load_state()
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler('start',  cmd_start))
    app.add_handler(CommandHandler('total',  cmd_total))
    app.add_handler(CommandHandler('check',  cmd_check))
    app.add_handler(CommandHandler('games',  cmd_games))
    app.add_handler(CommandHandler('stats',  cmd_stats))
    app.add_handler(CommandHandler('status', cmd_status))

    async def post_init(app):
        asyncio.create_task(monitor_loop(app))
    app.post_init = post_init

    log.info("Bot v3 started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
