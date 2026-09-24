"""
Matchpoint UTR Auto-Updater
Запуск: python3 update_utr.py
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
                utr = data.get("singlesUtr") or data.get("myUtrSingles")
                if utr and float(utr) > 0:
                    return float(utr)
        except:
            continue
    return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(script_dir, 'index.html')

    if not os.path.exists(index_path):
        print("ERROR: index.html not found")
        return

    with open(index_path, 'r') as f:
        content = f.read()

    # Read player data from embedded JSON
    match = re.search(r'<script id="player-data" type="application/json">(.*?)</script>', content, re.DOTALL)
    if not match:
        print("ERROR: No player data in index.html")
        print("Do Publish from editor.html first, then run this script")
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
            print(f"  skip  {p['name']:<28} no ID")
            continue

        print(f"  fetch {p['name']:<28} ID:{utr_id} ... ", end='', flush=True)
        new_utr = fetch_utr(utr_id)

        if new_utr:
            old_utr = p.get('utr', 0)
            if old_utr and old_utr != new_utr:
                p['prevUtr'] = old_utr
            p['utr'] = new_utr
            arrow = ""
            if old_utr:
                diff = new_utr - old_utr
                if diff > 0.01: arrow = f" ▲+{diff:.2f}"
                elif diff < -0.01: arrow = f" ▼{diff:.2f}"
            print(f"{new_utr:.2f}{arrow}")
            updated += 1
        else:
            print("not found")
        time.sleep(0.4)

    if updated == 0:
        print("\nNo updates. Exiting.")
        return

    # ONLY update the JSON data tag — nothing else in HTML
    new_data = json.dumps(players, ensure_ascii=False)
    new_content = re.sub(
        r'<script id="player-data" type="application/json">.*?</script>',
        f'<script id="player-data" type="application/json">{new_data}</script>',
        content,
        flags=re.DOTALL
    )

    with open(index_path, 'w') as f:
        f.write(new_content)

    print(f"\n{'='*45}")
    print(f"Updated: {updated} players")
    print(f"Saved. Now run: git add . && git commit -m 'Update UTR' && git push")
    print(f"{'='*45}\n")

if __name__ == "__main__":
    main()
