# Discord講座 進み具合の自動更新

Discord「Claude自動化講座」（Windows版・Mac版）で、各STEPの本文に ✅ を押した人を読み、

1. 進み具合シート（Google スプレッドシート「Claude自動化講座 進み具合」）に名前を足してチェックを付ける
2. 次のSTEPのロールを付けて、次の部屋を開く

を1時間ごとに行います。ロールを外す・メッセージを送る・消すことはしません。

## どこで動くか（Windows → Mac → GitHub）

| 順番 | どこで | いつ | 作業するとき |
| --- | --- | --- | --- |
| 1 | Windows（タスク スケジューラ） | 毎時5分 | いつも |
| 2 | Mac（launchd） | 毎時11分 | Windows が70分以上作業していないときだけ |
| 3 | GitHub Actions（クラウド） | 毎時17分 | Windows も Mac も130分以上作業していないときだけ |

だれが最後に作業したかは、シートの「状態」タブに自動で書かれます。二重には動きません。
threads-autopost などのランナーや、ほかの定期作業には触りません。

## 鍵の置き場所（ファイルやチャットには書かない）

- GitHub：Settings → Secrets and variables → Actions
  - Secrets：`DISCORD_TOKEN`（BOT のトークン）、`GOOGLE_SA_JSON`（サービスアカウントの JSON の中身）
  - Variables：`SHEET_ID`
- Windows / Mac：`python setup_keys.py` で、パソコンの鍵の保管庫に入れる（1回だけ）

## はじめの設定

1. **Discord BOT**（Discord Developer Portal）
   - Bot の「Privileged Gateway Intents」で **SERVER MEMBERS INTENT** をオン
   - 2つのサーバーに招待（権限：ロールの管理・チャンネルを見る・メッセージ履歴を読む）
   - サーバー設定 → ロールで、BOT のロールを **STEP1〜STEP7 より上** に置く
2. **Google サービスアカウント**（Google Cloud）
   - Google Sheets API をオン → サービスアカウントを作る → JSON の鍵を作る
   - 進み具合シートを、そのサービスアカウントのメール（…@….iam.gserviceaccount.com）に「編集者」で共有
3. **GitHub**：上の Secrets / Variables を入れる → Actions タブで「Run workflow」で試す
4. **Windows**：このリポジトリを置いて `python setup_keys.py` → `powershell -ExecutionPolicy Bypass -File install_windows.ps1`
5. **Mac**：このリポジトリを置いて `python3 setup_keys.py` → `bash install_mac.sh`

試すだけなら `python sync.py --role windows --dry`（何も書かずに、やることだけ表示）。
