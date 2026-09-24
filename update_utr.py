"""
Matchpoint UTR Auto-Updater
Запуск: python3 update_utr.py
Читает данные из index.html, тянет UTR, сохраняет обратно.
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

    # Read player data from embedded JSON script tag
    match = re.search(r'<script id="player-data" type="application/json">(.*?)<\/script>', content, re.DOTALL)
    if not match:
        print("ERROR: No player data found in index.html")
        print("Please do Publish from editor.html first")
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

    # Update player data in index.html
    new_data = json.dumps(players, ensure_ascii=False)
    new_content = re.sub(
        r'<script id="player-data" type="application/json">.*?<\/script>',
        f'<script id="player-data" type="application/json">{new_data}<\/script>',
        content, flags=re.DOTALL
    )

    # Also update the visual table
    sorted_players = sorted(players, key=lambda x: x.get('utr',0), reverse=True)
    rated = [p for p in players if p.get('utr',0)>0]
    avg = f"{sum(p['utr'] for p in rated)/len(rated):.2f}" if rated else "—"
    top = f"{max(p['utr'] for p in rated):.2f}" if rated else "—"
    elite = sum(1 for p in players if p.get('level')=='Elite')

    # Update stats
    new_content = re.sub(r'(<div class="stat-num">)\d+(\s*</div>\s*<div class="stat-label">Total)', 
                         f'\\g<1>{len(players)}\\2', new_content)

    with open(index_path, 'w') as f:
        f.write(new_content)

    print(f"\n{'='*45}")
    print(f"Updated: {updated} players")
    print(f"Saved to index.html — ready to git push")
    print(f"{'='*45}\n")

if __name__ == "__main__":
    main()
