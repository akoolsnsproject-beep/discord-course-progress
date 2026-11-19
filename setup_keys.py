"""Windows / Mac で1回だけ実行する：鍵をパソコンの鍵の保管庫（Windows 資格情報マネージャー / Mac キーチェーン）に入れる。
ファイルには書かない。入力した文字は画面に出ません。
すでに入っているものは、何も入れずに Enter を押すとそのまま使います。

  python setup_keys.py
"""
import getpass

import keyring

SERVICE = "discord-course-progress"
CHUNK = 800  # Windows の保管庫は1つに入る長さに上限があるので、長いものは小分けにする


def has(name):
    return bool(keyring.get_password(SERVICE, name) or keyring.get_password(SERVICE, f"{name}_n"))


def put_long(name, text):
    parts = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)]
    for i, p in enumerate(parts):
        keyring.set_password(SERVICE, f"{name}_{i}", p)
    keyring.set_password(SERVICE, f"{name}_n", str(len(parts)))


print("Discord BOT のトークンを貼り付けて Enter（画面には出ません）" + ("。入っているので、Enter だけでそのまま使います" if has("DISCORD_TOKEN") else ""))
v = getpass.getpass("> ").strip()
if v:
    keyring.set_password(SERVICE, "DISCORD_TOKEN", v)

print("Google サービスアカウントの JSON ファイルの場所を入力して Enter" + ("。入っているので、Enter だけでそのまま使います" if has("GOOGLE_SA_JSON") else ""))
path = input("> ").strip().strip('"')
if path:
    with open(path, encoding="utf-8") as f:
        put_long("GOOGLE_SA_JSON", f.read())
    print("入れました。JSON ファイルはもう消して大丈夫です（ゴミ箱も空にしてください）。")

print("進み具合シートの ID を入力して Enter" + ("。入っているので、Enter だけでそのまま使います" if has("SHEET_ID") else ""))
v = input("> ").strip()
if v:
    keyring.set_password(SERVICE, "SHEET_ID", v)
print("できました。")
