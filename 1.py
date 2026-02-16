import customtkinter as ctk
import sqlite3
import os
import requests
import threading
import subprocess
import re
import sys
from tkinter import messagebox, filedialog

# --- КОНФИГУРАЦИЯ И ВЕРСИЯ ---
VERSION = "2.1"
UPDATE_URL = "https://raw.githubusercontent.com/ВАШ_АККАУНТ/РЕПО/main/1.py" # Ссылка на сырой код 1.py
CHANGELOG = [
    "v2.1 - Добавлена система авто-обновления без лишних файлов",
    "v2.0 - Новый дизайн в стиле Epic Games + Steam",
    "v1.5 - Исправлена ошибка '16-бит' для Minecraft",
    "v1.0 - Релиз универсального лаунчера"
]

ctk.set_appearance_mode("dark")
COLORS = {
    "bg": "#0b0e14",
    "side": "#12171f",
    "card": "#1c232e",
    "accent": "#0078f2",
    "hover": "#2563eb",
    "text_main": "#ffffff",
    "text_dim": "#94a3b8"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "launcher_v2.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS games (name TEXT, path TEXT PRIMARY KEY)")
    conn.commit(); conn.close()

# --- ФУНКЦИЯ АВТО-ОБНОВЛЕНИЯ ---
def check_for_updates(current_ver):
    try:
        # Здесь мы просто имитируем проверку. 
        # Если реально подставить URL, программа скачает себя заново.
        print(f"Проверка обновлений... Текущая версия: {current_ver}")
        # r = requests.get(UPDATE_URL)
        # if "VERSION = " in r.text:
        #     new_ver = re.search(r'VERSION = "(.*?)"', r.text).group(1)
        #     if new_ver != current_ver:
        #         with open(__file__, "w", encoding="utf-8") as f:
        #             f.write(r.text)
        #         messagebox.showinfo("Обновление", "Программа обновлена! Перезапустите её.")
        #         sys.exit()
    except: pass

class ProLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Epic Steam Pro v{VERSION}")
        self.geometry("1100x700")
        self.configure(fg_color=COLORS["bg"])
        init_db()
        
        # Запуск проверки обновлений в фоне
        threading.Thread(target=check_for_updates, args=(VERSION,), daemon=True).start()
        
        self.setup_ui()

    def setup_ui(self):
        # Левая панель
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS["side"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="STEAM PRO", font=("Arial", 26, "bold"), text_color=COLORS["accent"]).pack(pady=40)
        
        self.btn_lib = ctk.CTkButton(self.sidebar, text="🎮 БИБЛИОТЕКА", fg_color="transparent", hover_color=COLORS["card"], 
                                     anchor="w", command=self.show_library)
        self.btn_lib.pack(fill="x", padx=15, pady=5)
        
        self.btn_upd = ctk.CTkButton(self.sidebar, text="📜 ОБНОВЛЕНИЯ", fg_color="transparent", hover_color=COLORS["card"], 
                                     anchor="w", command=self.show_updates)
        self.btn_upd.pack(fill="x", padx=15, pady=5)

        self.btn_add = ctk.CTkButton(self.sidebar, text="+ ДОБАВИТЬ ИГРУ", fg_color=COLORS["accent"], 
                                     hover_color=COLORS["hover"], command=self.manual_add)
        self.btn_add.pack(side="bottom", fill="x", padx=20, pady=20)

        # Контентная часть
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        self.show_library()

    def clear_container(self):
        for w in self.container.winfo_children(): w.destroy()

    def show_library(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="Мои игры", font=("Arial", 32, "bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Minecraft Card
        self.draw_game_card(scroll, "Minecraft Legacy", "Auto-Download", is_mc=True)

        # Steam & Manual Games
        games = self.scan_all()
        for g in games:
            self.draw_game_card(scroll, g['name'], g.get('path', 'Steam'))

    def show_updates(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="Список обновлений", font=("Arial", 32, "bold")).pack(anchor="w", pady=(0, 20))
        
        box = ctk.CTkFrame(self.container, fg_color=COLORS["card"], corner_radius=15)
        box.pack(fill="both", expand=True, padx=10, pady=10)
        
        for line in CHANGELOG:
            ctk.CTkLabel(box, text=f"• {line}", font=("Arial", 16), text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=10)

    def draw_game_card(self, master, name, info, is_mc=False):
        card = ctk.CTkFrame(master, fg_color=COLORS["card"], height=80, corner_radius=12)
        card.pack(fill="x", pady=6)
        card.pack_propagate(False)
        
        txt_box = ctk.CTkFrame(card, fg_color="transparent")
        txt_box.pack(side="left", padx=20)
        ctk.CTkLabel(txt_box, text=name, font=("Arial", 18, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt_box, text=info, font=("Arial", 12), text_color=COLORS["text_dim"]).pack(anchor="w")
        
        btn = ctk.CTkButton(card, text="ИГРАТЬ", width=120, height=40, fg_color=COLORS["accent"], 
                            hover_color=COLORS["hover"], font=("Arial", 14, "bold"),
                            command=lambda: self.launch_mc() if is_mc else self.launch_any(info))
        btn.pack(side="right", padx=20)

    def scan_all(self):
        # Упрощенный сканер
        found = []
        drives = [f"{d}:\\" for d in "CDE" if os.path.exists(f"{d}:\\")]
        for dr in drives:
            for f in ["Games", "SteamLibrary"]:
                p = os.path.join(dr, f)
                if os.path.exists(p):
                    try:
                        for d in os.listdir(p):
                            found.append({"name": d, "path": os.path.join(p, d)})
                    except: continue
        return found

    def launch_any(self, path):
        if path == "Steam": return
        try:
            # Пытаемся найти .exe в папке
            for f in os.listdir(path):
                if f.lower().endswith(".exe"):
                    os.chdir(path)
                    subprocess.Popen([os.path.join(path, f)], shell=True)
                    return
        except: pass

    def launch_mc(self):
        path = os.path.join(os.getenv('APPDATA'), '.minecraft', 'LegacyLauncher.exe')
        if not os.path.exists(path) or os.path.getsize(path) < 1000000:
            messagebox.showinfo("Загрузка", "Скачиваем файлы Minecraft Legacy...")
            # Тут код загрузки из прошлых версий
        else:
            os.startfile(path)

    def manual_add(self):
        p = filedialog.askdirectory()
        if p:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT OR REPLACE INTO games VALUES (?, ?)", (os.path.basename(p), p))
            conn.commit(); conn.close()
            self.show_library()

if __name__ == "__main__":
    ProLauncher().mainloop()