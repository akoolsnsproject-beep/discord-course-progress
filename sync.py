"""Claude自動化講座：Discord の ✅ を読んで、進み具合シートとロールを更新する。

動く順番（だれか1つだけが作業する）:
  1. windows  … いつも作業する
  2. mac      … Windows が 70 分以上作業していないときだけ
  3. github   … Windows も Mac も 130 分以上作業していないときだけ
だれが最後に作業したかは、シートの「状態」タブに書く。

鍵（Discord BOT のトークン・Google のサービスアカウント）は:
  - GitHub では Secrets（DISCORD_TOKEN / GOOGLE_SA_JSON）
  - Windows / Mac ではパソコンの鍵の保管庫（keyring）。ファイルには書かない。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.parse

import requests

JST = dt.timezone(dt.timedelta(hours=9))
API = "https://discord.com/api/v10"
CHECK = "✅"
KEYRING_SERVICE = "discord-course-progress"

# ---- 講座の設定 -------------------------------------------------------------
SERVERS = [
    {
        "os": "Windows",
        "guild": "1572461825553862656",
        "board": "1572846900611256441",  # 管理人だけが見る #進み具合ボード
        # (STEPの部屋のID, その部屋の本文メッセージのID) を STEP0〜7 の順に
        "steps": [
            ("1572463901684138104", "1572483841883644014"),
            ("1572464015832252497", "1572484121442132131"),
            ("1572464095939137607", "1572484367790506068"),
            ("1572464120316297396", "1572484609382289428"),
            ("1572464223563546794", "1572484855214768211"),
            ("1572464251581497447", "1572485095984468148"),
            ("1572464283529519225", "1572485341594648636"),
            ("1572464348708864120", "1572485584390459472"),
        ],
    },
    {
        "os": "Mac",
        "guild": "1572527079767937064",
        "board": "1572847068303859833",
        "steps": [
            ("1572527080502071460", "1572527603804282920"),
            ("1572527080502071461", "1572527719843897346"),
            ("1572527080502071462", "1572527834738593920"),
            ("1572527080502071463", "1572527947489747045"),
            ("1572527080502071464", "1572528060710912101"),
            ("1572527080502071465", "1572528172858351626"),
            ("1572527080715845683", "1572528286418862190"),
            ("1572527080715845684", "1572528405940015184"),
        ],
    },
]
OWNER_USERNAMES = {"riki102."}  # サーバー主（数えない）
SHEET_TAB = "進み具合"
STATE_TAB = "状態"
FIRST_ROW = 6  # 表の1行目（5行目が見出し）
# 列: A名前 B OS C進み具合 D次にやるSTEP E..L STEP0..7 M Discord名 N最終確認日 O メモ P ユーザーID
COL_STEP0 = 5   # E
COL_USER = 13   # M
COL_DATE = 14   # N
COL_ID = 16     # P

MAC_WAIT_MIN = 70
GITHUB_WAIT_MIN = 130


# ---- 鍵 -------------------------------------------------------------------
def secret(name: str) -> str:
    v = os.environ.get(name)
    if v:
        return v
    try:
        import keyring
        v = keyring.get_password(KEYRING_SERVICE, name)
        if not v:  # 長いもの（Google の JSON）は小分けにして入れてある
            n = keyring.get_password(KEYRING_SERVICE, f"{name}_n")
            if n:
                v = "".join(keyring.get_password(KEYRING_SERVICE, f"{name}_{i}") or "" for i in range(int(n)))
    except Exception:
        v = None
    if not v:
        sys.exit(f"鍵 {name} が見つかりません（README の「はじめの設定」を見てください）")
    return v


# ---- Discord --------------------------------------------------------------
class Discord:
    def __init__(self, token: str):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bot {token}"
        self.s.headers["User-Agent"] = "DiscordBot (course-progress, 1.0)"

    def req(self, method: str, path: str, **kw):
        for _ in range(5):
            r = self.s.request(method, API + path, timeout=30, **kw)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.5)
                continue
            r.raise_for_status()
            return r.json() if r.content else None
        r.raise_for_status()

    def members(self, guild: str):
        out, after = [], "0"
        while True:
            page = self.req("GET", f"/guilds/{guild}/members", params={"limit": 1000, "after": after})
            out += page
            if len(page) < 1000:
                return out
            after = page[-1]["user"]["id"]

    def roles(self, guild: str):
        return {r["name"]: r["id"] for r in self.req("GET", f"/guilds/{guild}/roles")}

    def reactors(self, channel: str, message: str):
        out, after = [], "0"
        emoji = urllib.parse.quote(CHECK)
        while True:
            page = self.req("GET", f"/channels/{channel}/messages/{message}/reactions/{emoji}",
                            params={"limit": 100, "after": after})
            out += page
            if len(page) < 100:
                return out
            after = page[-1]["id"]

    def update_board(self, channel: str, bot_id: str, text: str) -> str:
        """ボードの部屋の BOT の投稿を書きかえる（なければ新しく出す）。"""
        for m in self.req("GET", f"/channels/{channel}/messages", params={"limit": 20}):
            if m["author"]["id"] == bot_id:
                if m.get("content") == text:
                    return "same"
                self.req("PATCH", f"/channels/{channel}/messages/{m['id']}", json={"content": text})
                return "edited"
        self.req("POST", f"/channels/{channel}/messages", json={"content": text})
        return "posted"

    def add_role(self, guild: str, user: str, role: str):
        self.req("PUT", f"/guilds/{guild}/members/{user}/roles/{role}",
                 headers={"X-Audit-Log-Reason": "STEP clear (auto)"})


# ---- Google シート ----------------------------------------------------------
def open_sheet():
    import gspread
    info = json.loads(secret("GOOGLE_SA_JSON"))
    gc = gspread.service_account_from_dict(info)
    return gc.open_by_key(secret("SHEET_ID"))


def read_state(book):
    ws = book.worksheet(STATE_TAB)
    vals = dict(r[:2] for r in ws.get("A2:B4") if len(r) >= 2)
    return ws, vals


def parse_time(s: str | None):
    try:
        return dt.datetime.fromisoformat(s) if s else None
    except ValueError:
        return None


def minutes_since(t):
    return 1e9 if t is None else (dt.datetime.now(JST) - t).total_seconds() / 60


def my_turn(role: str, state: dict) -> bool:
    w = minutes_since(parse_time(state.get("windows")))
    m = minutes_since(parse_time(state.get("mac")))
    if role == "windows":
        return True
    if role == "mac":
        return w >= MAC_WAIT_MIN
    return w >= GITHUB_WAIT_MIN and m >= GITHUB_WAIT_MIN


# ---- 本体 -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=["windows", "mac", "github"], required=True)
    ap.add_argument("--dry", action="store_true", help="何も書かずに、やることだけ表示")
    a = ap.parse_args()

    book = open_sheet()
    state_ws, state = read_state(book)
    if not my_turn(a.role, state):
        print(f"{a.role}: ほかのパソコンが作業しているので、お休みします")
        return

    dc = Discord(secret("DISCORD_TOKEN"))
    bot_id = dc.req("GET", "/users/@me")["id"]
    today = dt.datetime.now(JST).strftime("%Y-%m-%d")

    ws = book.worksheet(SHEET_TAB)
    rows = ws.get(f"A{FIRST_ROW}:P", value_render_option="UNFORMATTED_VALUE")
    by_id, by_user, by_name = {}, {}, {}
    for i, r in enumerate(rows):
        r = r + [""] * (16 - len(r))
        rown = FIRST_ROW + i
        if r[COL_ID - 1]:
            by_id[str(r[COL_ID - 1])] = (rown, r)
        if r[COL_USER - 1]:
            by_user[str(r[COL_USER - 1])] = (rown, r)
        if r[0]:
            by_name[(str(r[0]), str(r[1]))] = (rown, r)
    next_empty = FIRST_ROW + next((i for i, r in enumerate(rows) if not (r and r[0])), len(rows))

    updates, log = [], []
    for srv in SERVERS:
        roles = dc.roles(srv["guild"])
        members = [m for m in dc.members(srv["guild"])
                   if not m["user"].get("bot") and m["user"]["username"] not in OWNER_USERNAMES]
        done = {m["user"]["id"]: set() for m in members}
        for step, (ch, msg_id) in enumerate(srv["steps"]):
            try:
                users = dc.reactors(ch, msg_id)
            except requests.HTTPError as e:
                log.append(f"{srv['os']} STEP{step}: ✅ を読めませんでした（{e.response.status_code}）")
                continue
            for u in users:
                if u["id"] in done:
                    done[u["id"]].add(step)

        people = []
        for m in members:
            uid, uname = m["user"]["id"], m["user"]["username"]
            name = m.get("nick") or m["user"].get("global_name") or uname
            hit = by_id.get(uid) or by_user.get(uname) or by_name.get((name, srv["os"]))
            if hit:
                rown, r = hit
            else:
                rown, r = next_empty, [""] * 16
                next_empty += 1
                updates.append({"range": f"A{rown}:B{rown}", "values": [[name, srv["os"]]]})
                updates.append({"range": f"M{rown}:N{rown}", "values": [[uname, today]]})
                log.append(f"追加：{name}（{srv['os']}）")
            if str(r[COL_ID - 1]) != uid:
                updates.append({"range": f"P{rown}", "values": [[uid]]})
            changed = False
            for step in sorted(done[uid]):
                col = COL_STEP0 + step
                if r[col - 1] is not True:
                    cell = gspread_a1(rown, col)
                    updates.append({"range": cell, "values": [[True]]})
                    changed = True
                    log.append(f"✅ {name}：STEP{step}")
                if step < 7:
                    role_id = roles.get(f"STEP{step + 1}")
                    if role_id and role_id not in m.get("roles", []):
                        if not a.dry:
                            dc.add_role(srv["guild"], uid, role_id)
                        log.append(f"🔓 {name}：STEP{step + 1} のロール")
            if changed and hit:
                updates.append({"range": f"N{rown}", "values": [[today]]})
            already = {i for i in range(8) if r[COL_STEP0 - 1 + i] is True}
            people.append((name, already | done[uid]))

        if srv.get("board") and not a.dry:
            try:
                res = dc.update_board(srv["board"], bot_id, board_text(srv["os"], people, secret("SHEET_ID")))
                if res != "same":
                    log.append(f"📊 {srv['os']} のボードを更新")
            except requests.HTTPError as e:
                log.append(f"📊 {srv['os']} のボードを更新できませんでした（{e.response.status_code}）")

    if a.dry:
        print("\n".join(log) or "変更なし（dry）")
        return
    if updates:
        ws.batch_update(updates, value_input_option="USER_ENTERED")
    now = dt.datetime.now(JST).isoformat(timespec="seconds")
    state_ws.update(range_name={"windows": "B2", "mac": "B3", "github": "B4"}[a.role], values=[[now]])
    print(f"{a.role}: " + ("\n".join(log) if log else "変更なし"))


STEP_NAMES = ["準備", "はじめてのAI", "プロンプトの型", "指示テンプレ",
              "Threads自動投稿", "インスタ自動投稿", "動画自動編集", "ジャービス"]


def board_text(os_name: str, people: list, sheet_id: str) -> str:
    """people: [(名前, 終わったSTEPの集合)]"""
    now = dt.datetime.now(JST).strftime("%m/%d %H:%M")
    total = len(people)
    allclear = sum(1 for _, d in people if len(d) == 8)
    at = [0] * 9  # 今いるSTEP（最初の終わっていないSTEP）。8 は全クリア
    rows = []
    for name, d in people:
        cur = next((i for i in range(8) if i not in d), 8)
        at[cur] += 1
        bar = "".join("✅" if i in d else "⬜" for i in range(8))
        pct = round(len(d) / 8 * 100)
        where = "🎉 全クリア" if cur == 8 else f"STEP{cur} {STEP_NAMES[cur]}"
        rows.append((len(d), f"`{bar}` {pct:>3}%  **{name}**　→ {where}"))
    rows.sort(key=lambda x: -x[0])
    head = [
        f"## 📊 進み具合ボード（{os_name}版）",
        f"メンバー **{total}人**　／　全クリア **{allclear}人**　（{now} 更新・1時間ごと）",
        "いる場所：" + "　".join(f"STEP{i} {at[i]}人" for i in range(8)) + f"　🎉 {at[8]}人",
        "",
    ]
    foot = ["", f"📄 くわしくは表 → <https://docs.google.com/spreadsheets/d/{sheet_id}/edit>"]
    body = [r for _, r in rows] or ["（まだメンバーはいません）"]
    out = head + body + foot
    while len("\n".join(out)) > 1900 and len(body) > 1:  # Discord の文字数の上限
        body = body[:-1]
        out = head + body + [f"…ほか {total - len(body)}人"] + foot
    return "\n".join(out)


def gspread_a1(row: int, col: int) -> str:
    s = ""
    while col:
        col, rem = divmod(col - 1, 26)
        s = chr(65 + rem) + s
    return f"{s}{row}"


if __name__ == "__main__":
    main()
