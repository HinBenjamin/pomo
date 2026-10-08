#!/usr/bin/env python3
"""
Pomodoro CLI interactif avec cases de progression [✓] [▶] [ ] [ ] et affichage grand format.
"""

import sys
import os
import re
import time
import curses
import argparse
import subprocess
import json
import unicodedata
from datetime import datetime, date

HISTORY_FILE = os.path.expanduser("~/.pomodoro_history.json")
STATE_FILE = os.path.expanduser("~/.pomodoro_state.json")

# Palette ANSI 24-bit moderne
C_RED = "\033[38;2;255;95;86m"
C_GREEN = "\033[38;2;39;201;63m"
C_YELLOW = "\033[38;2;255;189;46m"
C_BLUE = "\033[38;2;68;189;255m"
C_PURPLE = "\033[38;2;198;120;221m"
C_CYAN = "\033[38;2;86;182;194m"
C_MUTED = "\033[38;2;120;120;130m"
C_WHITE = "\033[97m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"

STYLES = {
    "boxes": {"done": "[✓]", "active": "[▶]", "todo": "[ ]"},
    "blocks": {"done": "[■]", "active": "[▣]", "todo": "[ ]"},
    "dots": {"done": "●", "active": "◐", "todo": "○"},
    "tomatoes": {"done": "🍅", "active": "⏳", "todo": "⚪"},
}

DIGITS_FONT = {
    '0': [" _ ", "/ \\", "\\_/"],
    '1': ["   ", " /|", "  |"],
    '2': [" _ ", " _|", "|_ "],
    '3': [" _ ", " _|", " _|"],
    '4': ["   ", "|_|", "  |"],
    '5': [" _ ", "|_ ", " _|"],
    '6': [" _ ", "|_ ", "|_|"],
    '7': [" _ ", "  |", "  |"],
    '8': [" _ ", "|_|", "|_|"],
    '9': [" _ ", "|_|", " _|"],
    ':': ["   ", " . ", " . "]
}

def render_big_digits(time_str: str) -> list[str]:
    """Génère de grands chiffres ASCII lisibles pour le minuteur."""
    try:
        from pyfiglet import Figlet
        f = Figlet(font='standard')
        rendered = f.renderText(time_str).splitlines()
        if len(rendered) >= 3:
            return rendered
    except Exception:
        pass
    
    # Fallback propre si pyfiglet n'est pas chargé
    lines = ["", "", ""]
    for char in time_str:
        glyph = DIGITS_FONT.get(char, ["   ", "   ", "   "])
        for i in range(3):
            lines[i] += glyph[i] + " "
    return lines

def visible_width(s: str) -> int:
    clean = re.sub(r"\033\[[0-9;]*m", "", s)
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") or ord(c) > 0x2600 else 1 for c in clean)

def notify(title: str, message: str, sound: str = "Glass"):
    """Envoie une notification système (macOS / Linux)."""
    try:
        if sys.platform == "darwin":
            escaped_title = title.replace('"', '\\"')
            escaped_msg = message.replace('"', '\\"')
            apple_script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
            subprocess.run(["osascript", "-e", apple_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            sound_path = f"/System/Library/Sounds/{sound}.aiff"
            if os.path.exists(sound_path):
                subprocess.run(["afplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", title, message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def speak(text: str):
    """Annonce vocale si disponible."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("linux"):
            subprocess.run(["spd-say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def render_cases(total: int, completed_count: int, is_active: bool = False, style_name: str = "boxes", with_color: bool = False) -> str:
    st = STYLES.get(style_name, STYLES["boxes"])
    symbols = []
    for i in range(total):
        if i < completed_count:
            sym = f"{C_GREEN}{st['done']}{C_RESET}" if with_color else st["done"]
        elif i == completed_count and is_active:
            sym = f"{C_RED}{C_BOLD}{st['active']}{C_RESET}" if with_color else st["active"]
        else:
            sym = f"{C_MUTED}{st['todo']}{C_RESET}" if with_color else st["todo"]
        symbols.append(sym)
    return " ".join(symbols)

def load_state() -> int:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == str(date.today()):
                    return int(data.get("completed_in_cycle", 0))
        except Exception:
            pass
    return 0

def save_state(completed_in_cycle: int):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"completed_in_cycle": completed_in_cycle, "date": str(date.today())}, f)
    except Exception:
        pass

def record_session(task: str, duration_min: int):
    try:
        data = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({
            "timestamp": datetime.now().isoformat(),
            "date": str(date.today()),
            "task": task or "Focus",
            "duration": duration_min
        })
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def show_stats(daily_goal: int = 8):
    if not os.path.exists(HISTORY_FILE):
        print(f"\n{C_MUTED}Aucune session enregistrée pour le moment.{C_RESET}\n")
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    today_str = str(date.today())
    today_sessions = [s for s in data if s.get("date") == today_str]
    today_count = len(today_sessions)
    today_minutes = sum(s.get("duration", 25) for s in today_sessions)
    today_hours = today_minutes / 60

    total_count = len(data)
    total_minutes = sum(s.get("duration", 25) for s in data)
    total_hours = total_minutes / 60

    pct = min(100, int((today_count / max(1, daily_goal)) * 100))
    bar_len = 14
    filled = int((pct / 100) * bar_len)
    bar = f"{C_GREEN}{'■' * filled}{C_MUTED}{'□' * (bar_len - filled)}{C_RESET}"

    w = 58
    print(f"\n{C_CYAN}╭{'─' * (w - 2)}╮{C_RESET}")
    print(f"{C_CYAN}│{C_RESET}  {C_BOLD}📊 TABLEAU DE BORD POMODORO{C_RESET}{' ' * (w - 31)}{C_CYAN}│{C_RESET}")
    print(f"{C_CYAN}├{'─' * (w - 2)}┤{C_RESET}")
    print(f"{C_CYAN}│{C_RESET}  {C_BOLD}📅 Aujourd'hui{C_RESET} : {C_GREEN}{C_BOLD}{today_count}{C_RESET} session(s)  •  {C_CYAN}{today_hours:.1f}h{C_RESET} ({today_minutes}m)")
    print(f"{C_CYAN}│{C_RESET}  {C_BOLD}🎯 Objectif   {C_RESET} : {bar} {C_BOLD}{pct}%{C_RESET} ({today_count}/{daily_goal})")
    print(f"{C_CYAN}│{C_RESET}  {C_BOLD}🏆 Total cumul{C_RESET} : {C_YELLOW}{total_count}{C_RESET} session(s)  •  {C_PURPLE}{total_hours:.1f}h{C_RESET} ({total_minutes}m)")
    print(f"{C_CYAN}├{'─' * (w - 2)}┤{C_RESET}")
    print(f"{C_CYAN}│{C_RESET}  {C_DIM}Dernières sessions du jour :{C_RESET}")

    if today_sessions:
        for s in today_sessions[-5:]:
            dt = datetime.fromisoformat(s["timestamp"]).strftime("%H:%M")
            task_name = s.get("task", "Focus")
            dur = s.get("duration", 25)
            print(f"{C_CYAN}│{C_RESET}    {C_MUTED}{dt}{C_RESET}  {C_GREEN}✓{C_RESET}  {C_WHITE}{task_name[:24]:<24}{C_RESET} {C_MUTED}({dur}m){C_RESET}")
    else:
        print(f"{C_CYAN}│{C_RESET}    {C_MUTED}Aucune session aujourd'hui.{C_RESET}")

    print(f"{C_CYAN}╰{'─' * (w - 2)}╯{C_RESET}\n")

def run_curses_timer(total_seconds: int, title_bar: str, cases_bar: str, is_break: bool = False) -> bool:
    """Affiche un écran de compte à rebours élégant avec bandeau et grands chiffres."""
    def _timer_loop(stdscr):
        try:
            curses.curs_set(0)
        except Exception:
            pass
        stdscr.nodelay(True)
        stdscr.timeout(100)

        # Initialisation couleurs curses
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_CYAN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)

        remaining = total_seconds
        last_tick = time.time()
        paused = False

        while remaining > 0:
            ch = stdscr.getch()
            if ch in (ord('q'), ord('Q')):
                return False
            elif ch == ord(' '):
                paused = not paused
            elif ch in (ord('+'), ord('=')):
                remaining += 60
            elif ch == ord('-'):
                remaining = max(1, remaining - 60)

            now = time.time()
            if not paused and now - last_tick >= 1.0:
                step = int(now - last_tick)
                remaining = max(0, remaining - step)
                last_tick = now

            mins = remaining // 60
            secs = remaining % 60
            time_display = f"{mins:02d}:{secs:02d}"

            stdscr.erase()
            h, w = stdscr.getmaxyx()

            # 1. Bandeau supérieur avec titre et cases bien visibles
            banner_line1 = f"  {title_bar}  "
            banner_line2 = f"  Progression : {cases_bar}  "
            
            box_w = max(len(banner_line1), len(banner_line2)) + 6
            start_x = max(0, (w - box_w) // 2)
            
            color_accent = curses.color_pair(3) if is_break else curses.color_pair(1)

            try:
                stdscr.addstr(1, start_x, "╭" + "─" * (box_w - 2) + "╮", color_accent)
                stdscr.addstr(2, start_x, "│", color_accent)
                stdscr.addstr(2, start_x + 2, banner_line1, curses.A_BOLD)
                stdscr.addstr(2, start_x + box_w - 1, "│", color_accent)

                stdscr.addstr(3, start_x, "│", color_accent)
                stdscr.addstr(3, start_x + 2, banner_line2)
                stdscr.addstr(3, start_x + box_w - 1, "│", color_accent)
                stdscr.addstr(4, start_x, "╰" + "─" * (box_w - 2) + "╯", color_accent)
            except Exception:
                pass

            # 2. Grands chiffres centrés
            big_digits = render_big_digits(time_display)
            digit_start_y = max(6, (h - len(big_digits)) // 2)
            for i, line in enumerate(big_digits):
                digit_x = max(0, (w - len(line)) // 2)
                try:
                    attr = curses.A_BOLD
                    if remaining <= 10:
                        attr |= curses.color_pair(1)
                    elif paused:
                        attr |= curses.color_pair(4)
                    stdscr.addstr(digit_start_y + i, digit_x, line, attr)
                except Exception:
                    pass

            # 3. Barre d'état inférieure
            status = " [PAUSE - Espace pour reprendre] " if paused else " [Espace] Pause  •  [+] +1m  •  [-] -1m  •  [q] Quitter "
            status_x = max(0, (w - len(status)) // 2)
            try:
                stdscr.addstr(min(h - 2, digit_start_y + len(big_digits) + 2), status_x, status, curses.A_DIM)
            except Exception:
                pass

            stdscr.refresh()
            time.sleep(0.05)

        return True

    try:
        return curses.wrapper(_timer_loop)
    except KeyboardInterrupt:
        return False

def main():
    parser = argparse.ArgumentParser(description="Pomodoro CLI élégant avec cases de session")
    parser.add_argument("work_pos", nargs="?", type=int, help="Durée de travail en minutes (ex: 25)")
    parser.add_argument("break_pos", nargs="?", type=int, help="Durée de pause courte en minutes (ex: 5)")
    parser.add_argument("-w", "--work", type=int, default=25, help="Durée de travail en minutes (défaut: 25)")
    parser.add_argument("-b", "--break-time", type=int, default=5, help="Pause courte en minutes (défaut: 5)")
    parser.add_argument("-l", "--long-break", type=int, default=15, help="Pause longue en minutes (défaut: 15)")
    parser.add_argument("-n", "--sessions", type=int, default=4, help="Nombre de sessions par cycle (défaut: 4)")
    parser.add_argument("-t", "--task", type=str, default="", help="Nom de la tâche / projet")
    parser.add_argument("-s", "--style", choices=list(STYLES.keys()), default="boxes", help="Style : boxes, blocks, dots, tomatoes")
    parser.add_argument("--auto", action="store_true", help="Enchaîne travail et pauses sans confirmation")
    parser.add_argument("--voice", action="store_true", help="Annonce vocale macOS/Linux")
    parser.add_argument("--stats", action="store_true", help="Affiche le tableau de bord des statistiques")
    parser.add_argument("--done", type=int, nargs="?", const=1, default=None, help="Nombre de sessions déjà faites (ex: --done ou --done 2)")
    parser.add_argument("--start", type=int, default=None, help="Numéro de session de départ (ex: 3)")
    parser.add_argument("--add", type=int, nargs="?", const=1, default=None, help="Ajoute N session(s) manuellement à l'historique")
    parser.add_argument("--record-done", action="store_true", help="Enregistre aussi les sessions de --done dans l'historique")
    parser.add_argument("--reset", action="store_true", help="Réinitialise le cycle de cases à 0")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    work_time = args.work_pos if args.work_pos is not None else args.work
    task = args.task.strip()

    if args.add is not None:
        count = args.add
        for _ in range(count):
            record_session(task, work_time)
        print(f"\n{C_GREEN}{C_BOLD}✓ {count} session(s) de {work_time}m ajoutée(s) à l'historique{C_RESET}" + (f" {C_MUTED}(Tâche : '{task}'){C_RESET}" if task else "") + ".")
        show_stats()
        return

    if args.reset:
        save_state(0)
        empty_cases = render_cases(args.sessions, 0, is_active=False, style_name=args.style, with_color=True)
        print(f"\n{C_YELLOW}⟲ Cycle réinitialisé :{C_RESET} {empty_cases}\n")
        return

    short_break = args.break_pos if args.break_pos is not None else args.break_time
    long_break = args.long_break
    total_sessions = args.sessions
    style = args.style

    # Prise en compte de --done et --start
    if args.done is not None:
        completed_in_cycle = max(0, min(args.done, total_sessions - 1))
        save_state(completed_in_cycle)
        if args.record_done:
            for _ in range(args.done):
                record_session(task, work_time)
            print(f"{C_GREEN}✓ {args.done} session(s) passée(s) enregistrée(s) dans l'historique.{C_RESET}")
    elif args.start is not None:
        completed_in_cycle = max(0, min(args.start - 1, total_sessions - 1))
        save_state(completed_in_cycle)
    else:
        completed_in_cycle = load_state()
        if completed_in_cycle >= total_sessions:
            completed_in_cycle = 0
            save_state(0)

    try:
        while True:
            # 1. Déroulement Session de Travail
            cases_display = render_cases(total_sessions, completed_in_cycle, is_active=True, style_name=style, with_color=False)
            task_str = f" • [{task}]" if task else ""
            title_work = f"🍅 SESSION {completed_in_cycle + 1}/{total_sessions}{task_str}"

            completed = run_curses_timer(work_time * 60, title_work, cases_display, is_break=False)
            if not completed:
                print(f"\n{C_YELLOW}Session interrompue.{C_RESET}\n")
                break

            # Incrémentation et validation immédiate de la session
            completed_in_cycle += 1
            save_state(completed_in_cycle)
            record_session(task, work_time)

            if args.voice:
                speak("Session terminée, prenez une pause.")
            notify("🍅 Pomodoro Terminé !", f"Session {completed_in_cycle}/{total_sessions} finie. Prends une pause.", "Glass")

            # 2. Déroulement Pause
            is_long = (completed_in_cycle >= total_sessions)
            break_duration = long_break if is_long else short_break
            break_label = "🎉 LONGUE PAUSE" if is_long else "☕ PAUSE COURTE"

            cases_break = render_cases(total_sessions, completed_in_cycle, is_active=False, style_name=style, with_color=False)
            cases_break_color = render_cases(total_sessions, completed_in_cycle, is_active=False, style_name=style, with_color=True)

            print(f"\n{C_GREEN}{C_BOLD}✓ Session {completed_in_cycle}/{total_sessions} validée !{C_RESET} {cases_break_color}")

            if not args.auto:
                try:
                    prompt = (
                        f"  {C_BOLD}👉 [Entrée]{C_RESET} Démarrer la {break_label.lower()} ({break_duration}m)  "
                        f"•  {C_MUTED}[s]{C_RESET} Sauter  "
                        f"•  {C_MUTED}[q]{C_RESET} Quitter : "
                    )
                    action = input(prompt).strip().lower()
                    if action == "q":
                        break
                    elif action == "s":
                        pass
                    else:
                        completed = run_curses_timer(break_duration * 60, break_label, cases_break, is_break=True)
                        if not completed:
                            break
                        if args.voice:
                            speak("Pause terminée, retour au travail.")
                        notify(f"{break_label} terminée !", "Prêt pour la prochaine session ?", "Hero")
                except EOFError:
                    break
            else:
                completed = run_curses_timer(break_duration * 60, break_label, cases_break, is_break=True)
                if not completed:
                    break
                if args.voice:
                    speak("Pause terminée.")
                notify(f"{break_label} terminée !", "Prêt pour la prochaine session ?", "Hero")

            # Réinitialisation après le cycle complet
            if completed_in_cycle >= total_sessions:
                completed_in_cycle = 0
                save_state(0)
                print(f"\n{C_PURPLE}{C_BOLD}🎉 Cycle complet terminé avec succès !{C_RESET}\n")

            if not args.auto:
                try:
                    next_num = completed_in_cycle + 1
                    prompt_next = (
                        f"  {C_BOLD}👉 [Entrée]{C_RESET} Lancer la session {next_num}/{total_sessions}  "
                        f"•  {C_MUTED}[q]{C_RESET} Quitter : "
                    )
                    rep = input(prompt_next).strip().lower()
                    if rep == "q":
                        break
                except EOFError:
                    break

    except KeyboardInterrupt:
        print(f"\n\n{C_YELLOW}Arrêt du Pomodoro.{C_RESET}")
    finally:
        print(f"\n{C_CYAN}À bientôt ! 👋{C_RESET}\n")

if __name__ == "__main__":
    main()
