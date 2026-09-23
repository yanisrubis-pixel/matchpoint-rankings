"""
Matchpoint UTR Auto-Updater
Запуск: python3 update_utr.py
Тянет UTR всех игроков с utrsports.net и обновляет index.html
"""

import requests
import json
import re
import time
import sys
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.utrsports.net/",
}

def fetch_utr(utr_id):
    urls = [
        f"https://app.universaltennis.com/api/v1/player/{utr_id}/profile",
        f"https://api.utrsports.net/v2/player/{utr_id}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                utr = (data.get("singlesUtr") or
                       data.get("myUtrSingles") or
                       data.get("utrSingles"))
                if utr and float(utr) > 0:
                    name = f"{data.get('firstName','')} {data.get('lastName','')}".strip()
                    return float(utr), name
        except:
            continue
    return None, None

def main():
    # Find index.html
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(script_dir, 'index.html')

    if not os.path.exists(index_path):
        print("ERROR: index.html not found")
        return

    with open(index_path, 'r') as f:
        content = f.read()

    # Extract players from index.html
    match = re.search(r'const players = (\[.*?\]);', content, re.DOTALL)
    if not match:
        print("ERROR: No players data found in index.html")
        return

    players = json.loads(match.group(1))
    print(f"\nMatchpoint UTR Updater")
    print(f"=" * 40)
    print(f"Total players: {len(players)}")
    
    with_id = [p for p in players if p.get('utrId') and str(p.get('utrId')).strip()]
    print(f"With UTR ID:   {len(with_id)}")
    print(f"=" * 40)

    updated = 0
    for p in players:
        utr_id = str(p.get('utrId', '')).strip()
        if not utr_id:
            print(f"  skip  {p['name']:<30} no ID")
            continue

        print(f"  fetch {p['name']:<30} ID:{utr_id} ... ", end='', flush=True)
        new_utr, site_name = fetch_utr(utr_id)

        if new_utr:
            old_utr = p.get('utr', 0)
            if old_utr and old_utr != new_utr:
                p['prevUtr'] = old_utr
            p['utr'] = new_utr
            diff = f" (▲+{new_utr-old_utr:.2f})" if old_utr and new_utr > old_utr else \
                   f" (▼{new_utr-old_utr:.2f})" if old_utr and new_utr < old_utr else ""
            print(f"UTR {new_utr:.2f}{diff}")
            updated += 1
        else:
            print("not found")

        time.sleep(0.4)

    # Save back to index.html
    new_data = json.dumps(players, ensure_ascii=False)
    new_content = re.sub(
        r'const players = \[.*?\];',
        f'const players = {new_data};',
        content,
        flags=re.DOTALL
    )

    with open(index_path, 'w') as f:
        f.write(new_content)

    print(f"\n{'=' * 40}")
    print(f"Updated: {updated} players")
    print(f"Saved to index.html")
    print(f"{'=' * 40}\n")

if __name__ == "__main__":
    main()
