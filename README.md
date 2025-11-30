# iTunes → EAC CD情報自動転送システム v2.0

iTunesで取得したCD情報をEAC（Exact Audio Copy）で利用可能な形式に変換し、リッピング作業を効率化するGUIアプリケーション。

## 主な機能

- iTunesからCD情報を自動取得
- Web検索による日本語タイトル自動取得（Wikipedia、MusicBrainz）
- CDPLAYER.INIファイルの自動生成
- EACとの連携
- トラック情報の手動編集・一括置換
- 検索結果のキャッシュ機能

## システム要件

- Windows 10/11
- Python 3.8以上
- iTunes for Windows（Microsoft Store版は非推奨）
- EAC 1.0以降
- インターネット接続（邦題検索機能使用時）

## インストール

1. Python 3.8以上をインストール
2. 必要ライブラリをインストール:
   ```bash
   pip install -r requirements.txt
   ```
3. `config.ini`でiTunesとEACのパスを設定

## 使用方法

1. `itunes_to_eac_gui.py`を実行
2. CDをドライブに挿入
3. [1. iTunesでCD情報取得]をクリック
4. [1-B. 日本語タイトル検索]で邦題を取得（オプション）
5. [2. CDPLAYER.INI生成]をクリック
6. [3. EACで読み込み]をクリック

詳細は仕様書を参照してください。

## ライセンス

MIT License

