"""iTunes制御モジュール"""

import time
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

try:
    import win32com.client
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False

try:
    import win32api
    import win32process
    WIN32API_AVAILABLE = True
except ImportError:
    WIN32API_AVAILABLE = False

from models.cd_info import CDInfo
from models.track import Track


class iTunesController:
    """iTunes制御クラス"""
    
    def __init__(self, itunes_path: str, startup_wait: int = 10, cd_recognition_wait: int = 5):
        """
        初期化
        
        Args:
            itunes_path: iTunes実行ファイルのパス
            startup_wait: 起動待機時間（秒）
            cd_recognition_wait: CD認識待機時間（秒）
        """
        self.itunes_path = Path(itunes_path)
        self.startup_wait = startup_wait
        self.cd_recognition_wait = cd_recognition_wait
        self.logger = logging.getLogger(__name__)
        self.app: Optional[object] = None
    
    def is_available(self) -> bool:
        """iTunesが利用可能かチェック"""
        if not WIN32COM_AVAILABLE:
            self.logger.error("pywin32がインストールされていません")
            return False
        return True
    
    def _check_process_running(self) -> bool:
        """
        プロセス名でiTunesの起動を検出
        
        Returns:
            iTunesプロセスが実行中かどうか
        """
        try:
            # tasklistコマンドでiTunes.exeプロセスを検索
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq iTunes.exe', '/FO', 'CSV', '/NH'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and 'iTunes.exe' in result.stdout:
                self.logger.debug("iTunesプロセスを検出しました")
                return True
            else:
                self.logger.debug("iTunesプロセスが見つかりませんでした")
                return False
        except Exception as e:
            self.logger.debug(f"プロセス検出エラー: {e}")
            return False
    
    def _get_com_object(self, retry_count: int = 3, retry_interval: float = 1.0) -> Tuple[Optional[object], bool]:
        """
        COMオブジェクトを取得（リトライ付き）
        
        Args:
            retry_count: リトライ回数
            retry_interval: リトライ間隔（秒）
        
        Returns:
            (COMオブジェクト, 成功したかどうか)
        """
        if not WIN32COM_AVAILABLE:
            return None, False
        
        for attempt in range(retry_count):
            try:
                # 複数のProgIDを試行
                prog_ids = ["iTunes.Application", "iTunes.Application.1"]
                
                for prog_id in prog_ids:
                    try:
                        self.logger.debug(f"COMオブジェクト取得を試行中: {prog_id} (試行 {attempt + 1}/{retry_count})")
                        app = win32com.client.Dispatch(prog_id)
                        self.logger.info(f"COMオブジェクトを取得しました: {prog_id}")
                        return app, True
                    except Exception as e:
                        self.logger.debug(f"ProgID {prog_id} で失敗: {e}")
                        continue
                
                # すべてのProgIDで失敗した場合
                if attempt < retry_count - 1:
                    self.logger.debug(f"COMオブジェクト取得に失敗。{retry_interval}秒後に再試行します...")
                    time.sleep(retry_interval)
                    
            except Exception as e:
                self.logger.debug(f"COMオブジェクト取得エラー（試行 {attempt + 1}/{retry_count}）: {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_interval)
        
        return None, False
    
    def start(self) -> bool:
        """
        iTunesを起動（ハイブリッド方式）
        
        Returns:
            成功したかどうか
        """
        if not self.is_available():
            self.logger.error("pywin32が利用できません")
            return False
        
        # 既に起動しているかチェック（プロセス検出）
        if self._check_process_running():
            self.logger.info("iTunesプロセスは既に起動しています")
            # COMオブジェクト取得を試行（リトライ付き）
            com_app, com_success = self._get_com_object(retry_count=3, retry_interval=1.0)
            if com_success and com_app:
                self.app = com_app
                self.logger.info("iTunes COMオブジェクトを取得しました")
                return True
            else:
                self.logger.warning("iTunesプロセスは起動していますが、COMオブジェクトに接続できません")
                self.logger.warning("CD情報の取得にはCOMオブジェクトが必要です")
                return False
        
        # COMオブジェクト取得を試行（既に起動している可能性）
        com_app, com_success = self._get_com_object(retry_count=1, retry_interval=0.5)
        if com_success and com_app:
            self.app = com_app
            self.logger.info("iTunes COMオブジェクトを取得しました（既に起動中）")
            return True
        
        # 実行ファイルから起動を試みる
        if self.itunes_path.exists():
            try:
                self.logger.info(f"iTunesを起動します: {self.itunes_path}")
                subprocess.Popen([str(self.itunes_path)])
                self.logger.info(f"iTunes起動待機中... ({self.startup_wait}秒)")
                time.sleep(self.startup_wait)
                
                # 再度COMオブジェクトを取得（リトライ付き）
                com_app, com_success = self._get_com_object(retry_count=3, retry_interval=1.0)
                if com_success and com_app:
                    self.app = com_app
                    self.logger.info("iTunesを起動し、COMオブジェクトを取得しました")
                    return True
                else:
                    self.logger.error("iTunesは起動しましたが、COMオブジェクトに接続できませんでした")
                    import traceback
                    self.logger.error(f"詳細なエラー情報:\n{traceback.format_exc()}")
            except Exception as e2:
                self.logger.error(f"iTunes起動エラー（実行ファイル経由）: {e2}")
                import traceback
                self.logger.error(traceback.format_exc())
        else:
            self.logger.error(f"iTunes実行ファイルが見つかりません: {self.itunes_path}")
        
        return False
    
    def is_running(self) -> bool:
        """
        iTunesが起動中かチェック（ハイブリッド方式）
        プロセス検出とCOMオブジェクト取得の両方で判定
        
        Returns:
            iTunesが起動中かどうか
        """
        # まずプロセスで検出
        process_running = self._check_process_running()
        
        # COMオブジェクト取得を試行
        com_app, com_success = self._get_com_object(retry_count=1, retry_interval=0.5)
        
        if com_success and com_app:
            # COMオブジェクトが取得できた場合は保存
            self.app = com_app
            self.logger.debug("iTunes起動中（COMオブジェクト取得成功）")
            return True
        
        # プロセスは起動しているがCOMが失敗する場合
        if process_running:
            self.logger.warning("iTunesプロセスは起動していますが、COMオブジェクトに接続できません")
            self.logger.warning("Microsoft Store版のiTunesを使用している可能性があります")
            # プロセスが起動していれば「起動中」と判定
            return True
        
        # プロセスも起動していない
        self.logger.debug("iTunesは起動していません")
        return False
    
    def stop(self) -> bool:
        """
        iTunesを終了
        
        Returns:
            成功したかどうか
        """
        if not self.app:
            return True
        
        try:
            self.app.Quit()
            self.app = None
            self.logger.info("iTunesを終了しました")
            return True
        except Exception as e:
            self.logger.error(f"iTunes終了エラー: {e}")
            return False
    
    def _refresh_cd_source(self, cd_source) -> bool:
        """
        CDソースをリフレッシュして再読み込みを試みる
        
        Args:
            cd_source: CDソースオブジェクト
        
        Returns:
            成功したかどうか
        """
        try:
            # Refreshメソッドが存在するか確認
            if hasattr(cd_source, 'Refresh'):
                self.logger.info("CDソースをリフレッシュ中...")
                cd_source.Refresh()
                time.sleep(2)  # リフレッシュ後の待機
                return True
            elif hasattr(cd_source, 'Update'):
                self.logger.info("CDソースを更新中...")
                cd_source.Update()
                time.sleep(2)
                return True
            else:
                self.logger.debug("CDソースにRefresh/Updateメソッドがありません")
                return False
        except Exception as e:
            self.logger.warning(f"CDソースのリフレッシュに失敗: {e}")
            return False
    
    def get_cd_info(self) -> Optional[CDInfo]:
        """
        CD情報を取得
        
        Returns:
            CD情報、取得失敗時はNone
        """
        # COMオブジェクトを取得（既に起動している場合も含む）
        if not self.app:
            # まずプロセスで起動状態を確認
            process_running = self._check_process_running()
            
            if process_running:
                self.logger.info("iTunesプロセスは起動しています。COMオブジェクトを取得します...")
            else:
                self.logger.info("iTunesを起動してCOMオブジェクトを取得します...")
            
            if not self.start():
                # プロセスは起動しているがCOMが失敗する場合の詳細なメッセージ
                if process_running:
                    self.logger.error("iTunesプロセスは起動していますが、COMオブジェクトに接続できませんでした")
                    self.logger.error("Microsoft Store版のiTunesを使用している場合、COMオブジェクトが利用できない可能性があります")
                    self.logger.error("通常インストール版のiTunesを使用するか、管理者権限で実行してください")
                else:
                    self.logger.error("iTunesの起動に失敗しました")
                    self.logger.error("iTunesが正しくインストールされているか確認してください")
                return None
        
        # 念のため再度確認
        if not self.app:
            self.logger.error("iTunes COMオブジェクトが取得できませんでした")
            return None
        
        try:
            self.logger.debug("iTunes COMオブジェクトにアクセス中...")
            
            # CDソースを取得
            sources = self.app.Sources
            self.logger.debug(f"ソース数: {sources.Count}")
            
            cd_source = None
            
            # CDソースを検索（Kind 1または3がCDソース）
            for i in range(1, sources.Count + 1):
                try:
                    source = sources.Item(i)
                    source_kind = source.Kind
                    source_name = source.Name
                    self.logger.debug(f"ソース {i}: {source_name} (Kind: {source_kind})")
                    
                    # Kind 3は物理CD、Kind 1はライブラリ（CDが挿入されている場合も含む）
                    if source_kind == 3:
                        # Kind 3は確実にCDソース
                        cd_source = source
                        self.logger.info(f"CDソースを検出しました（Kind 3）: {source_name}")
                        break
                    elif source_kind == 1:
                        # Kind 1の場合は、プレイリストを確認してCDかどうかを判定
                        playlists = source.Playlists
                        if playlists.Count > 0:
                            # 「ライブラリ」以外のプレイリストを探す
                            for j in range(1, min(playlists.Count + 1, 10)):  # 最初の10個まで確認
                                try:
                                    playlist = playlists.Item(j)
                                    playlist_name = playlist.Name
                                    
                                    # ライブラリではなく、トラックがあるプレイリストならCDと判断
                                    if playlist_name != "ライブラリ" and playlist.Tracks.Count > 0:
                                        cd_source = source
                                        self.logger.info(f"CDソースを検出しました（Kind 1）: {source_name} (プレイリスト: {playlist_name})")
                                        break
                                except:
                                    continue
                            
                            if cd_source:
                                break
                except Exception as e:
                    self.logger.debug(f"ソース {i} 情報取得エラー: {e}")
                    continue
            
            if not cd_source:
                self.logger.warning("CDが検出されませんでした。CDが挿入されているか確認してください。")
                return None
            
            # CDソースをリフレッシュして再読み込みを試みる
            self.logger.info("CDソースの再読み込みを試みます...")
            self._refresh_cd_source(cd_source)
            
            # CD認識待機
            self.logger.info(f"CD認識待機中... ({self.cd_recognition_wait}秒)")
            time.sleep(self.cd_recognition_wait)
            
            # プレイリストを取得（最大2回試行）
            max_retries = 2
            cd_playlist = None
            
            for retry in range(max_retries):
                playlists = cd_source.Playlists
                self.logger.debug(f"プレイリスト数: {playlists.Count} (試行 {retry + 1}/{max_retries})")
                
                if playlists.Count == 0:
                    if retry < max_retries - 1:
                        self.logger.info("プレイリストが見つかりません。再試行します...")
                        # 再度リフレッシュを試みる
                        self._refresh_cd_source(cd_source)
                        time.sleep(2)
                        continue
                    else:
                        self.logger.warning("CDプレイリストが見つかりませんでした。CDが正しく認識されていない可能性があります。")
                        return None
                
                # CDプレイリストを探す（「ライブラリ」以外のプレイリスト）
                for i in range(1, playlists.Count + 1):
                    try:
                        playlist = playlists.Item(i)
                        playlist_name = playlist.Name
                        self.logger.debug(f"プレイリスト {i}: {playlist_name} (トラック数: {playlist.Tracks.Count})")
                        
                        # 「ライブラリ」以外で、トラックがあるプレイリストをCDと判断
                        if playlist_name != "ライブラリ" and playlist.Tracks.Count > 0:
                            cd_playlist = playlist
                            self.logger.info(f"CDプレイリストを検出: {playlist_name}")
                            break
                    except Exception as e:
                        self.logger.debug(f"プレイリスト {i} の取得に失敗: {e}")
                        continue
                
                # CDプレイリストが見つかった場合はループを抜ける
                if cd_playlist:
                    break
                
                # 見つからない場合は最初のプレイリストを使用（最後の試行時のみ）
                if retry == max_retries - 1:
                    try:
                        cd_playlist = playlists.Item(1)
                        self.logger.warning(f"CDプレイリストが見つからないため、最初のプレイリストを使用: {cd_playlist.Name}")
                    except:
                        pass
            
            if not cd_playlist:
                self.logger.error("CDプレイリストを取得できませんでした")
                return None
            
            self.logger.debug(f"使用するプレイリスト: {cd_playlist.Name}")
            
            # アルバム情報を取得
            album = cd_playlist.Name
            artist = ""
            genre = ""
            year = ""
            
            # トラック情報を取得
            tracks = []
            try:
                track_collection = cd_playlist.Tracks
                track_count = track_collection.Count
                self.logger.debug(f"トラック数: {track_count}")
                
                if track_count == 0:
                    self.logger.warning("トラックが0件です")
                    return None
                
                # COMコレクションは1から始まるインデックスを使用
                for idx in range(1, track_count + 1):
                    try:
                        track_obj = track_collection.Item(idx)
                        track_name = track_obj.Name or f"Track {idx}"
                        track_artist = track_obj.Artist or ""
                        track_duration = track_obj.Duration or 0
                        
                        self.logger.debug(f"トラック{idx}: {track_name} - {track_artist} ({track_duration}秒)")
                        
                        if not artist and track_artist:
                            artist = track_artist
                        if not genre and hasattr(track_obj, 'Genre') and track_obj.Genre:
                            genre = track_obj.Genre
                        if not year and hasattr(track_obj, 'Year') and track_obj.Year:
                            year = str(track_obj.Year)
                        
                        track = Track(
                            number=idx,
                            title=track_name,
                            title_en=track_name,
                            artist=track_artist or artist,
                            duration=int(float(track_duration))
                        )
                        tracks.append(track)
                    except Exception as e:
                        self.logger.warning(f"トラック{idx}の取得に失敗: {e}")
                        import traceback
                        self.logger.debug(traceback.format_exc())
                        continue
            except Exception as e:
                self.logger.error(f"トラックコレクションの取得に失敗: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                return None
            
            if not tracks:
                self.logger.warning("トラック情報が取得できませんでした")
                self.logger.warning("既読CDの場合、iTunesが自動的にトラック情報を読み込まない可能性があります。")
                self.logger.warning("CDを一度取り出して再挿入するか、iTunesで手動でCDを読み込んでください。")
                return None
            
            # CDInfoオブジェクトを作成
            cd_info = CDInfo(
                artist=artist or "Unknown Artist",
                album=album or "Unknown Album",
                genre=genre,
                year=year,
                tracks=tracks
            )
            cd_info.language = cd_info.detect_language()
            
            self.logger.info(f"CD情報を取得しました: {cd_info.artist} - {cd_info.album} ({len(tracks)}トラック)")
            return cd_info
        
        except Exception as e:
            self.logger.error(f"CD情報取得エラー: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

