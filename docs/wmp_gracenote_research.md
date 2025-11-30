# Windows Media Player経由でのGracenoteデータ取得に関する調査

## 調査日
2025年11月30日

## 調査目的
iTunes以外でGracenoteにアクセスしてCD情報を取得する方法として、Windows Media Player（WMP）の実現可能性を調査。

## 調査結果

### 1. Windows Media PlayerでのGracenoteデータ取得の可能性

#### 技術的な可能性: 中程度

**実現可能な点**:
1. **COM APIの存在**
   - Windows Media PlayerはCOM APIを提供
   - `WMPlayer.OCX`経由でアクセス可能
   - Pythonの`win32com.client`で操作可能

2. **CD情報の取得**
   - WMPのCOM APIでCDコレクションにアクセス可能
   - トラック情報、アルバム名、アーティスト名などを取得可能

3. **Gracenoteデータの利用**
   - WMPはGracenoteのデータベースを利用（間接的）
   - CDを挿入すると自動的にメタデータを取得

### 2. 制約・課題

#### 2.1 直接的なGracenoteアクセスではない
- WMPはMicrosoftのサービス（`musicmatch-ssl.xboxlive.com`）経由で情報を取得
- Gracenoteに直接アクセスしているわけではない
- 取得できる情報はWMPが取得したものに限られる

#### 2.2 COM APIの制約
- iTunesのCOM APIと比較して機能が限定的
- CD情報の取得方法が異なる可能性
- エラーハンドリングが複雑

#### 2.3 Windows 10/11での対応状況
- Windows Media PlayerはWindows 10/11でも利用可能
- ただし、機能が縮小されている可能性
- 将来のサポートが不透明

#### 2.4 ライセンス・利用規約
- WMP経由で取得したデータの再利用に制限がある可能性
- 商用利用には注意が必要

### 3. 実装上の考慮事項

#### メリット
- iTunesが不要
- Windows標準機能のため追加インストール不要
- COM APIでアクセス可能

#### デメリット
- iTunesのCOM APIより機能が限定的
- 取得できる情報の精度がiTunesより低い可能性
- エラーハンドリングが複雑
- 将来のサポートが不透明

### 4. その他のGracenoteアクセス方法

#### 4.1 既存のアプリケーション
1. **Windows Media Player**
   - Windows標準のメディアプレーヤー
   - GracenoteのCDトラック識別サービスを利用

2. **x-アプリ（Music Center for PC）**
   - ソニー製の音楽管理ソフト
   - Gracenoteと連携してアルバム名、曲名、ジャケット写真などを取得

3. **カーナビゲーションシステム**
   - 三菱電機、パナソニックなどの一部カーナビ
   - Gracenoteデータベースを利用して楽曲情報を取得

#### 4.2 開発者向けのアクセス方法
- **Gracenote Developer API**
  - 商用利用にはライセンス契約が必要
  - 個人開発者向けには制限がある可能性
  - APIキーの取得が必要

#### 4.3 代替案
- **MusicBrainz**: オープンソースの音楽メタデータベース（現在のアプリで使用中）
- **freedb/CDDB**: オープンソースのCDデータベース
- **Discogs API**: 音楽データベースのAPI

### 5. 推奨事項

#### 現状のアプローチ（iTunes + Web検索）の方が有利
- iTunesのCOM APIは機能が充実
- ハイブリッド検出方式でMicrosoft Store版にも対応
- Web検索（Wikipedia/MusicBrainz）で邦題も取得可能

#### Windows Media Playerを検討する場合
- iTunesが利用できない環境での代替案として検討
- 実装前に動作確認が必要
- 機能制限を理解した上で実装

## 結論

**技術的には可能だが、iTunesのCOM APIと比べて機能や情報の精度で劣る可能性が高い。**

現状のアプローチ（iTunes + Web検索）を継続することを推奨。

## 参考情報

- Windows Media Player COM API: https://learn.microsoft.com/ja-jp/windows/win32/wmp/windows-media-player-object-model
- Gracenote Developer API: https://developer.gracenote.com/
- MusicBrainz: https://musicbrainz.org/

