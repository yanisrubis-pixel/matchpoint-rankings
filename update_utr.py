"""
Matchpoint UTR Auto-Updater
Запуск: python3 update_utr.py
Тянет UTR всех игроков и обновляет editor.html
"""

import requests, json, re, time, os
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.utrsports.net/",
}

def fetch_utr(utr_id):
    for url in [
        f"https://app.universaltennis.com/api/v1/player/{utr_id}/profile",
        f"https://api.utrsports.net/v2/player/{utr_id}",
    ]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                utr = data.get("singlesUtr") or data.get("myUtrSingles") or data.get("utrSingles")
                if utr and float(utr) > 0:
                    return float(utr)
        except:
            continue
    return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    editor_path = os.path.join(script_dir, 'editor.html')

    if not os.path.exists(editor_path):
        print("ERROR: editor.html not found in", script_dir)
        return

    with open(editor_path, 'r') as f:
        content = f.read()

    # Find players data in editor.html
    match = re.search(r'const DEFAULT_PLAYERS = (\[.*?\]);', content, re.DOTALL)
    if not match:
        print("ERROR: No players data found in editor.html")
        return

    players = json.loads(match.group(1))
    with_id = [p for p in players if str(p.get('utrId','')).strip()]

    print(f"\nMatchpoint UTR Updater — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*45}")
    print(f"Total: {len(players)}  |  With UTR ID: {len(with_id)}")
    print(f"{'='*45}")

    updated = 0
    for p in players:
        utr_id = str(p.get('utrId', '')).strip()
        if not utr_id:
            print(f"  ⏭  {p['name']:<28} no ID")
            continue

        print(f"  ↓  {p['name']:<28} ID:{utr_id} ... ", end='', flush=True)
        new_utr = fetch_utr(utr_id)

        if new_utr:
            old_utr = p.get('utr', 0)
            if old_utr and old_utr != new_utr:
                p['prevUtr'] = old_utr
            p['utr'] = new_utr
            arrow = f" ▲+{new_utr-old_utr:.2f}" if old_utr and new_utr > old_utr else \
                    f" ▼{new_utr-old_utr:.2f}" if old_utr and new_utr < old_utr else ""
            print(f"{new_utr:.2f}{arrow}")
            updated += 1
        else:
            print("not found")

        time.sleep(0.4)

    # Save back to editor.html
    new_data = json.dumps(players, ensure_ascii=False)
    new_content = re.sub(
        r'const DEFAULT_PLAYERS = \[.*?\];',
        f'const DEFAULT_PLAYERS = {new_data};',
        content, flags=re.DOTALL
    )

    with open(editor_path, 'w') as f:
        f.write(new_content)

    print(f"\n{'='*45}")
    print(f"Updated: {updated} players")
    print(f"Saved to editor.html")
    print(f"\nТеперь открой editor.html → нажми Publish → запусти git push")
    print(f"{'='*45}\n")

if __name__ == "__main__":
    main()
