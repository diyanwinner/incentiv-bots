# scripts/galxe_watch.py
import os, json, re
import requests
from bs4 import BeautifulSoup

TARGET_URL = os.getenv("TARGET_URL")
STATE_FILE = os.getenv("STATE_FILE", ".state/galxe_nethara.json")
BOT = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

def send_tg(msg: str):
    if not (BOT and CHAT):
        print("Telegram env not set; skip send.")
        return
    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    requests.post(url, json={"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}, timeout=30)

def fetch_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.text

def extract_quest_ids(html: str):
    ids = set()
    for m in re.finditer(r"/quest/[A-Za-z0-9]+/([A-Za-z0-9]+)", html):
        ids.add(m.group(1))
    for m in re.finditer(r'"questId"\s*:\s*"([A-Za-z0-9]+)"', html):
        ids.add(m.group(1))
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        if "/quest/" in a["href"]:
            mm = re.search(r"/quest/[A-Za-z0-9]+/([A-Za-z0-9]+)", a["href"])
            if mm:
                ids.add(mm.group(1))
    return sorted(ids)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"seen_ids": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    html = fetch_html(TARGET_URL)
    ids = extract_quest_ids(html)

    state = load_state()
    seen = set(state.get("seen_ids", []))

    new_ids = [i for i in ids if i not in seen]
    if new_ids:
        msg = (
            "🆕 <b>Nethara Labs — New Galxe Task detected</b>\n"
            f"URL: {TARGET_URL}\n"
            f"New quest IDs: {', '.join(new_ids)}"
        )
        send_tg(msg)
        state["seen_ids"] = sorted(set(seen).union(ids))
        save_state(state)
        print("New tasks found:", new_ids)
    else:
        print("No new tasks.")

if __name__ == "__main__":
    main()
