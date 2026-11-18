"""Windows / Mac で1回だけ実行する：鍵をパソコンの鍵の保管庫（Windows 資格情報マネージャー / Mac キーチェーン）に入れる。
ファイルには書かない。入力した文字は画面に出ません。

  python setup_keys.py
"""
import getpass

import keyring

SERVICE = "discord-course-progress"

print("Discord BOT のトークンを貼り付けて Enter（画面には出ません）")
keyring.set_password(SERVICE, "DISCORD_TOKEN", getpass.getpass("> ").strip())

print("Google サービスアカウントの JSON ファイルの場所を入力して Enter")
path = input("> ").strip().strip('"')
with open(path, encoding="utf-8") as f:
    keyring.set_password(SERVICE, "GOOGLE_SA_JSON", f.read())
print("入れました。JSON ファイルはもう消して大丈夫です（ゴミ箱も空にしてください）。")

print("進み具合シートの ID（URL の /d/ と /edit の間）を入力して Enter")
keyring.set_password(SERVICE, "SHEET_ID", input("> ").strip())
print("できました。")
