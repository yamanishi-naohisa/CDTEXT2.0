"""iTunes接続テストスクリプト"""

import sys
import traceback

try:
    import win32com.client
    print("✓ pywin32が利用可能です")
except ImportError:
    print("✗ pywin32がインストールされていません")
    sys.exit(1)

print("\n=== iTunes COM API接続テスト ===\n")

try:
    # iTunes COMオブジェクトを取得
    print("1. iTunes COMオブジェクトを取得中...")
    app = win32com.client.Dispatch("iTunes.Application")
    print("   ✓ 成功: iTunes COMオブジェクトを取得しました")
    
    # バージョン情報を取得
    try:
        version = app.Version
        print(f"   iTunesバージョン: {version}")
    except:
        print("   ⚠ バージョン情報の取得に失敗")
    
    # ソース一覧を取得
    print("\n2. ソース一覧を取得中...")
    sources = app.Sources
    print(f"   ソース数: {sources.Count}")
    
    cd_source = None
    for i in range(1, sources.Count + 1):
        try:
            source = sources.Item(i)
            source_kind = source.Kind
            source_name = source.Name
            print(f"   ソース {i}: {source_name} (Kind: {source_kind})")
            
            if source_kind == 1:  # CDソース
                cd_source = source
                print(f"   ✓ CDソースを検出: {source_name}")
        except Exception as e:
            print(f"   ⚠ ソース {i} の取得に失敗: {e}")
    
    if not cd_source:
        print("\n   ✗ CDソースが見つかりませんでした")
        print("   確認事項:")
        print("   - CDがドライブに挿入されているか")
        print("   - iTunesでCDが認識されているか")
    else:
        # プレイリストを取得
        print("\n3. CDプレイリストを取得中...")
        playlists = cd_source.Playlists
        print(f"   プレイリスト数: {playlists.Count}")
        
        if playlists.Count == 0:
            print("   ✗ CDプレイリストが見つかりませんでした")
        else:
            cd_playlist = playlists.Item(1)
            playlist_name = cd_playlist.Name
            print(f"   プレイリスト名: {playlist_name}")
            
            # トラック情報を取得
            print("\n4. トラック情報を取得中...")
            tracks = cd_playlist.Tracks
            track_count = tracks.Count
            print(f"   トラック数: {track_count}")
            
            if track_count == 0:
                print("   ✗ トラックが見つかりませんでした")
            else:
                print("\n   トラック一覧:")
                for i in range(1, min(track_count + 1, 6)):  # 最初の5トラックのみ表示
                    try:
                        track = tracks.Item(i)
                        track_name = track.Name or f"Track {i}"
                        track_artist = track.Artist or "Unknown"
                        track_duration = track.Duration or 0
                        print(f"   {i:02d}. {track_name} - {track_artist} ({int(track_duration)}秒)")
                    except Exception as e:
                        print(f"   ⚠ トラック {i} の取得に失敗: {e}")
                
                if track_count > 5:
                    print(f"   ... (他 {track_count - 5} トラック)")
                
                print("\n   ✓ CD情報の取得に成功しました！")
    
    print("\n=== テスト完了 ===")
    
except Exception as e:
    print(f"\n✗ エラーが発生しました: {e}")
    print("\n詳細なエラー情報:")
    traceback.print_exc()
    sys.exit(1)

