"""iTunes → EAC CD情報転送ツール v2.0 メインGUIアプリケーション"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import os
import logging
from pathlib import Path
from typing import Optional

from models.cd_info import CDInfo
from models.track import Track
from controllers.itunes_controller import iTunesController
from controllers.eac_controller import EACController
from generators.cdplayer_generator import CDPlayerGenerator
from search.web_search_manager import WebSearchManager
from utils.config_manager import ConfigManager
from utils.logger import setup_logger, get_logger
from utils.history_manager import HistoryManager


class iTunesToEACGUI:
    """メインGUIアプリケーションクラス"""
    
    def __init__(self):
        """初期化"""
        # 設定読み込み
        self.config = ConfigManager()
        
        # ロガー設定（デバッグ用にDEBUGレベルに設定可能）
        log_level = self.config.get('Options', 'log_level', fallback='INFO')
        # デバッグ時は以下のコメントを外してDEBUGレベルに設定
        # log_level = 'DEBUG'
        self.logger = setup_logger(log_level=log_level)
        
        # 履歴管理
        self.history = HistoryManager()
        
        # コントローラー初期化
        self.itunes_controller = iTunesController(
            itunes_path=self.config.get('Paths', 'itunes_path'),
            startup_wait=self.config.getint('Options', 'itunes_startup_wait', fallback=10),
            cd_recognition_wait=self.config.getint('Options', 'cd_recognition_wait', fallback=5)
        )
        
        self.eac_controller = EACController(
            eac_path=self.config.get('Paths', 'eac_path')
        )
        
        # 生成器初期化
        self.cdplayer_generator = CDPlayerGenerator(
            encoding=self.config.get('Encoding', 'cdplayer_encoding', fallback='shift_jis')
        )
        
        # Web検索マネージャー初期化
        search_config = {
            'use_wikipedia_ja': self.config.getboolean('WebSearch', 'use_wikipedia_ja', fallback=True),
            'use_musicbrainz': self.config.getboolean('WebSearch', 'use_musicbrainz', fallback=True),
            'use_general_search': self.config.getboolean('WebSearch', 'use_general_search', fallback=False),
            'search_timeout': self.config.getint('WebSearch', 'search_timeout', fallback=30),
            'max_candidates': self.config.getint('WebSearch', 'max_candidates', fallback=5),
            'enable_cache': self.config.getboolean('Cache', 'enable_cache', fallback=True),
            'cache_dir': self.config.get('Cache', 'cache_dir', fallback='cache'),
            'cache_expire_days': self.config.getint('Cache', 'cache_expire_days', fallback=30)
        }
        self.web_search_manager = WebSearchManager(search_config)
        
        # CD情報
        self.cd_info: Optional[CDInfo] = None
        
        # GUI構築
        self.root = tk.Tk()
        self.root.title("iTunes → EAC CD情報転送ツール v2.0")
        self.root.geometry("900x700")
        
        self._create_menu()
        self._create_widgets()
        
        # 状態更新
        self.update_status()
    
    def _create_menu(self):
        """メニューバーを作成"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル (F)", menu=file_menu)
        file_menu.add_command(label="設定 (S)", command=self.show_settings)
        file_menu.add_command(label="履歴表示 (H)", command=self.show_history)
        file_menu.add_command(label="検索キャッシュをクリア", command=self.clear_cache)
        file_menu.add_separator()
        file_menu.add_command(label="終了 (X)", command=self.on_closing)
        
        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集 (E)", menu=edit_menu)
        edit_menu.add_command(label="トラック情報を編集 (E)", command=self.edit_track)
        edit_menu.add_command(label="すべて原題に戻す (R)", command=self.reset_all_titles)
        edit_menu.add_command(label="一括置換 (B)", command=self.bulk_replace)
        
        # ツールメニュー
        tool_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール (T)", menu=tool_menu)
        tool_menu.add_command(label="CDPLAYER.INIを開く", command=self.open_cdplayer_ini)
        tool_menu.add_command(label="ログフォルダを開く", command=self.open_log_folder)
        tool_menu.add_command(label="手動更新 (R)", command=self.refresh_cd_info)
        tool_menu.add_command(label="検索エンジン設定", command=self.show_search_settings)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ (H)", menu=help_menu)
        help_menu.add_command(label="使い方 (U)", command=self.show_help)
        help_menu.add_command(label="邦題検索について", command=self.show_search_help)
        help_menu.add_command(label="バージョン情報 (A)", command=self.show_version)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # アプリケーション制御パネル
        app_frame = ttk.LabelFrame(main_frame, text="アプリケーション制御", padding="5")
        app_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # iTunes制御
        ttk.Label(app_frame, text="iTunes:").grid(row=0, column=0, padx=5)
        self.itunes_status_label = ttk.Label(app_frame, text="○未起動")
        self.itunes_status_label.grid(row=0, column=1, padx=5)
        ttk.Button(app_frame, text="起動", command=self.start_itunes).grid(row=0, column=2, padx=5)
        ttk.Button(app_frame, text="終了", command=self.stop_itunes).grid(row=0, column=3, padx=5)
        
        # EAC制御
        ttk.Label(app_frame, text="EAC:").grid(row=1, column=0, padx=5, pady=5)
        self.eac_status_label = ttk.Label(app_frame, text="○未起動")
        self.eac_status_label.grid(row=1, column=1, padx=5)
        ttk.Button(app_frame, text="起動", command=self.start_eac).grid(row=1, column=2, padx=5)
        ttk.Button(app_frame, text="終了", command=self.stop_eac).grid(row=1, column=3, padx=5)
        
        # CD情報パネル
        cd_frame = ttk.LabelFrame(main_frame, text="CD情報", padding="5")
        cd_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(1, weight=1)
        
        # 状態表示
        self.cd_status_label = ttk.Label(cd_frame, text="状態: 未取得")
        self.cd_status_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # アルバム情報
        ttk.Label(cd_frame, text="アーティスト:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.artist_label = ttk.Label(cd_frame, text="")
        self.artist_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(cd_frame, text="アルバム:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.album_label = ttk.Label(cd_frame, text="")
        self.album_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(cd_frame, text="トラック数:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.track_count_label = ttk.Label(cd_frame, text="")
        self.track_count_label.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # 言語インジケータ
        self.language_label = ttk.Label(cd_frame, text="言語: -")
        self.language_label.grid(row=3, column=2, sticky=tk.W, padx=5)
        
        # トラックリスト
        track_frame = ttk.Frame(cd_frame)
        track_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        cd_frame.rowconfigure(4, weight=1)
        cd_frame.columnconfigure(1, weight=1)
        
        # ツリービュー
        columns = ('#', '原題', '邦題', '信頼度')
        self.track_tree = ttk.Treeview(track_frame, columns=columns, show='headings', height=10)
        self.track_tree.heading('#', text='#')
        self.track_tree.heading('原題', text='原題')
        self.track_tree.heading('邦題', text='邦題')
        self.track_tree.heading('信頼度', text='信頼度')
        self.track_tree.column('#', width=50)
        self.track_tree.column('原題', width=200)
        self.track_tree.column('邦題', width=200)
        self.track_tree.column('信頼度', width=80)
        
        scrollbar = ttk.Scrollbar(track_frame, orient=tk.VERTICAL, command=self.track_tree.yview)
        self.track_tree.configure(yscrollcommand=scrollbar.set)
        
        self.track_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        track_frame.rowconfigure(0, weight=1)
        track_frame.columnconfigure(0, weight=1)
        
        # トラックリスト右クリックメニュー
        self.track_menu = tk.Menu(self.root, tearoff=0)
        self.track_menu.add_command(label="このトラックを編集", command=self.edit_track)
        self.track_menu.add_command(label="Web検索", command=self.search_track)
        self.track_menu.add_command(label="原題に戻す", command=self.reset_track_title)
        self.track_tree.bind("<Button-3>", self.show_track_menu)
        self.track_tree.bind("<Double-1>", lambda e: self.edit_track())
        
        # 操作パネル
        action_frame = ttk.LabelFrame(main_frame, text="操作", padding="5")
        action_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(action_frame, text="1. iTunesでCD情報取得",
                  command=self.get_cd_info).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.search_button = ttk.Button(action_frame, text="1-B. 日本語タイトル検索 🌐",
                                       command=self.search_japanese_titles, state=tk.DISABLED)
        self.search_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(action_frame, text="2. CDPLAYER.INI生成",
                  command=self.generate_cdplayer_ini).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(action_frame, text="3. EACで読み込み",
                  command=self.load_to_eac).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(action_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        action_frame.columnconfigure(0, weight=1)
        
        # ログ/ステータスパネル
        log_frame = ttk.LabelFrame(main_frame, text="ログ/ステータス", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(3, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # ログハンドラを追加
        log_handler = TextHandler(self.log_text)
        log_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        log_handler.setLevel(logging.DEBUG)  # DEBUGレベルも表示
        self.logger.addHandler(log_handler)
    
    def update_status(self):
        """状態を更新"""
        # iTunes状態
        if self.itunes_controller.is_running():
            self.itunes_status_label.config(text="●起動中")
        else:
            self.itunes_status_label.config(text="○未起動")
        
        # EAC状態
        if self.eac_controller.is_running():
            self.eac_status_label.config(text="●起動中")
        else:
            self.eac_status_label.config(text="○未起動")
        
        # CD情報表示
        if self.cd_info:
            self.artist_label.config(text=self.cd_info.artist)
            self.album_label.config(text=self.cd_info.album)
            self.track_count_label.config(text=str(self.cd_info.num_tracks))
            
            # 言語表示
            lang = self.cd_info.detect_language()
            if lang == 'ja':
                self.language_label.config(text="言語: ✓ 日本語")
            elif lang == 'en':
                self.language_label.config(text="言語: 🌐 日本語化推奨")
                self.search_button.config(state=tk.NORMAL)
            elif lang == 'mixed':
                self.language_label.config(text="言語: 🌐 一部日本語化")
                self.search_button.config(state=tk.NORMAL)
            else:
                self.language_label.config(text="言語: -")
            
            # トラックリスト更新
            self.update_track_list()
        else:
            self.artist_label.config(text="")
            self.album_label.config(text="")
            self.track_count_label.config(text="")
            self.language_label.config(text="言語: -")
            self.track_tree.delete(*self.track_tree.get_children())
    
    def update_track_list(self):
        """トラックリストを更新"""
        self.track_tree.delete(*self.track_tree.get_children())
        
        if not self.cd_info:
            return
        
        for track in self.cd_info.tracks:
            title_ja = track.title_ja if track.title_ja else "[未取得]"
            confidence = track.get_confidence_stars() if track.title_ja else ""
            
            self.track_tree.insert('', 'end', values=(
                f"{track.number:02d}",
                track.title_en[:30] + "..." if len(track.title_en) > 30 else track.title_en,
                title_ja[:30] + "..." if len(title_ja) > 30 else title_ja,
                confidence
            ))
    
    def start_itunes(self):
        """iTunesを起動"""
        def _start():
            if self.itunes_controller.start():
                self.logger.info("iTunes起動完了")
                self.update_status()
            else:
                messagebox.showerror("エラー", "iTunesの起動に失敗しました")
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_itunes(self):
        """iTunesを終了"""
        if self.itunes_controller.stop():
            self.logger.info("iTunes終了完了")
            self.update_status()
        else:
            messagebox.showerror("エラー", "iTunesの終了に失敗しました")
    
    def start_eac(self):
        """EACを起動"""
        if self.eac_controller.start():
            self.logger.info("EAC起動完了")
            self.update_status()
        else:
            messagebox.showerror("エラー", "EACの起動に失敗しました")
    
    def stop_eac(self):
        """EACを終了"""
        if self.eac_controller.stop():
            self.logger.info("EAC終了完了")
            self.update_status()
        else:
            messagebox.showerror("エラー", "EACの終了に失敗しました")
    
    def get_cd_info(self):
        """CD情報を取得"""
        def _get():
            self.progress_var.set(0)
            self.logger.info("CD情報取得を開始...")
            
            # iTunesが起動しているか確認
            if not self.itunes_controller.is_running():
                self.logger.info("iTunesが起動していません。起動を試みます...")
            
            cd_info = self.itunes_controller.get_cd_info()
            
            if cd_info:
                self.cd_info = cd_info
                self.cd_status_label.config(text="状態: ✓ 情報取得完了")
                self.logger.info(f"CD情報取得完了: {cd_info.artist} - {cd_info.album}")
                self.update_status()
                self.progress_var.set(100)
            else:
                self.logger.error("CD情報の取得に失敗しました")
                error_msg = (
                    "CD情報の取得に失敗しました\n\n"
                    "以下の点を確認してください:\n"
                    "1. CDがドライブに正しく挿入されている\n"
                    "2. iTunesが起動している\n"
                    "3. iTunesでCDが認識されている\n"
                    "4. 詳細はログを確認してください"
                )
                messagebox.showerror("エラー", error_msg)
                self.progress_var.set(0)
        
        threading.Thread(target=_get, daemon=True).start()
    
    def search_japanese_titles(self):
        """日本語タイトルを検索"""
        if not self.cd_info:
            messagebox.showwarning("警告", "先にCD情報を取得してください")
            return
        
        def _search():
            self.progress_var.set(0)
            self.logger.info("日本語タイトル検索を開始...")
            
            def progress_callback(current, total):
                self.progress_var.set((current / total) * 50)
            
            # 検索実行
            search_results = self.web_search_manager.search_titles(
                self.cd_info,
                progress_callback=progress_callback
            )
            
            if not search_results:
                self.logger.warning("検索結果が見つかりませんでした")
                messagebox.showinfo("情報", "検索結果が見つかりませんでした")
                self.progress_var.set(0)
                return
            
            # マッチングと適用
            self.progress_var.set(50)
            self.cd_info = self.web_search_manager.apply_search_results(
                self.cd_info,
                search_results,
                auto_apply=False  # 手動確認モード
            )
            
            self.logger.info(f"邦題検索完了: {sum(1 for t in self.cd_info.tracks if t.title_ja)}/{len(self.cd_info.tracks)}件取得")
            self.update_status()
            self.progress_var.set(100)
            
            messagebox.showinfo("完了", f"邦題検索が完了しました\n{sum(1 for t in self.cd_info.tracks if t.title_ja)}/{len(self.cd_info.tracks)}件の邦題を取得しました")
        
        threading.Thread(target=_search, daemon=True).start()
    
    def generate_cdplayer_ini(self):
        """CDPLAYER.INIを生成"""
        if not self.cd_info:
            messagebox.showwarning("警告", "先にCD情報を取得してください")
            return
        
        output_path = self.config.get('Paths', 'cdplayer_output', fallback='')
        if not output_path:
            output_path = None
        
        if self.cdplayer_generator.generate(self.cd_info, output_path):
            self.logger.info("CDPLAYER.INI生成完了")
            messagebox.showinfo("完了", "CDPLAYER.INIを生成しました")
            
            # 履歴に追加
            self.history.add(self.cd_info)
        else:
            messagebox.showerror("エラー", "CDPLAYER.INIの生成に失敗しました")
    
    def load_to_eac(self):
        """EACで読み込み"""
        if not self.eac_controller.is_available():
            messagebox.showerror("エラー", "EACが見つかりません\n設定でパスを確認してください")
            return
        
        if not self.eac_controller.is_running():
            if not self.eac_controller.start():
                messagebox.showerror("エラー", "EACの起動に失敗しました")
                return
        
        messagebox.showinfo("情報", "EACが起動しました\nEACでCD情報を確認してください")
        self.logger.info("EACで読み込み完了")
    
    def edit_track(self):
        """トラックを編集"""
        selection = self.track_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集するトラックを選択してください")
            return
        
        item = self.track_tree.item(selection[0])
        track_num = int(item['values'][0])
        
        if not self.cd_info:
            return
        
        track = self.cd_info.tracks[track_num - 1]
        
        # 編集ダイアログ（簡易版）
        dialog = tk.Toplevel(self.root)
        dialog.title("トラック情報編集")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text=f"トラック: {track_num:02d}").pack(pady=10)
        
        ttk.Label(dialog, text="原題:").pack(anchor=tk.W, padx=20)
        title_en_entry = ttk.Entry(dialog, width=40)
        title_en_entry.insert(0, track.title_en)
        title_en_entry.pack(padx=20, pady=5)
        title_en_entry.config(state=tk.DISABLED)
        
        ttk.Label(dialog, text="邦題:").pack(anchor=tk.W, padx=20)
        title_ja_entry = ttk.Entry(dialog, width=40)
        if track.title_ja:
            title_ja_entry.insert(0, track.title_ja)
        title_ja_entry.pack(padx=20, pady=5)
        
        def save():
            title_ja = title_ja_entry.get().strip()
            if title_ja:
                track.set_japanese_title(title_ja, "manual", 100)
            else:
                track.clear_japanese_title()
            self.update_status()
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=save).pack(pady=10)
        ttk.Button(dialog, text="キャンセル", command=dialog.destroy).pack()
    
    def search_track(self):
        """選択トラックを検索"""
        messagebox.showinfo("情報", "個別トラック検索機能は今後実装予定です")
    
    def reset_track_title(self):
        """選択トラックの邦題をリセット"""
        selection = self.track_tree.selection()
        if not selection:
            return
        
        item = self.track_tree.item(selection[0])
        track_num = int(item['values'][0])
        
        if self.cd_info:
            track = self.cd_info.tracks[track_num - 1]
            track.clear_japanese_title()
            self.update_status()
    
    def reset_all_titles(self):
        """全トラックの邦題をリセット"""
        if not self.cd_info:
            return
        
        if messagebox.askyesno("確認", "すべての邦題を原題に戻しますか？"):
            for track in self.cd_info.tracks:
                track.clear_japanese_title()
            self.update_status()
    
    def bulk_replace(self):
        """一括置換"""
        messagebox.showinfo("情報", "一括置換機能は今後実装予定です")
    
    def show_track_menu(self, event):
        """トラックリストの右クリックメニューを表示"""
        self.track_menu.post(event.x_root, event.y_root)
    
    def show_settings(self):
        """設定ダイアログを表示"""
        messagebox.showinfo("情報", "設定ダイアログは今後実装予定です")
    
    def show_history(self):
        """履歴表示"""
        history_window = tk.Toplevel(self.root)
        history_window.title("CD処理履歴")
        history_window.geometry("600x400")
        
        tree = ttk.Treeview(history_window, columns=('日時', 'アーティスト', 'アルバム', 'トラック数', 'ステータス'), show='headings')
        tree.heading('日時', text='日時')
        tree.heading('アーティスト', text='アーティスト')
        tree.heading('アルバム', text='アルバム')
        tree.heading('トラック数', text='トラック数')
        tree.heading('ステータス', text='ステータス')
        
        for entry in self.history.get_latest(50):
            tree.insert('', 'end', values=(
                entry.get('date', '')[:19],
                entry.get('artist', ''),
                entry.get('album', ''),
                entry.get('tracks_count', 0),
                entry.get('status', '')
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        if messagebox.askyesno("確認", "検索キャッシュをすべて削除しますか？"):
            self.web_search_manager.cache.clear_all()
            messagebox.showinfo("完了", "キャッシュをクリアしました")
    
    def open_cdplayer_ini(self):
        """CDPLAYER.INIを開く"""
        output_path = self.config.get('Paths', 'cdplayer_output', fallback='')
        if not output_path:
            output_path = Path.home() / "CDPLAYER.INI"
        else:
            output_path = Path(output_path)
        
        if output_path.exists():
            os.startfile(output_path.parent)
        else:
            messagebox.showwarning("警告", "CDPLAYER.INIが見つかりません")
    
    def open_log_folder(self):
        """ログフォルダを開く"""
        log_dir = Path("logs")
        if log_dir.exists():
            os.startfile(log_dir)
        else:
            messagebox.showwarning("警告", "ログフォルダが見つかりません")
    
    def refresh_cd_info(self):
        """CD情報を再取得"""
        self.get_cd_info()
    
    def show_search_settings(self):
        """検索エンジン設定"""
        messagebox.showinfo("情報", "検索エンジン設定は今後実装予定です")
    
    def show_help(self):
        """ヘルプを表示"""
        help_text = """
使い方:

1. CDをドライブに挿入
2. [1. iTunesでCD情報取得]をクリック
3. [1-B. 日本語タイトル検索]で邦題を取得（オプション）
4. [2. CDPLAYER.INI生成]をクリック
5. [3. EACで読み込み]をクリック

詳細はREADME.mdを参照してください。
        """
        messagebox.showinfo("使い方", help_text)
    
    def show_search_help(self):
        """邦題検索について"""
        help_text = """
邦題検索機能:

- Wikipedia日本語版とMusicBrainzから日本語タイトルを自動検索します
- 検索結果はキャッシュに保存され、次回以降は高速に取得できます
- 信頼度スコア（★★★/★★/★）で検索結果の精度を表示します
- 手動で編集・確認が可能です
        """
        messagebox.showinfo("邦題検索について", help_text)
    
    def show_version(self):
        """バージョン情報"""
        messagebox.showinfo("バージョン情報", "iTunes → EAC CD情報転送ツール v2.0\n\nMIT License")
    
    def on_closing(self):
        """アプリケーション終了"""
        if messagebox.askokcancel("終了", "アプリケーションを終了しますか？"):
            self.root.destroy()
    
    def run(self):
        """アプリケーションを実行"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


class TextHandler(logging.Handler):
    """ログをテキストウィジェットに出力するハンドラ"""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        """ログレコードを出力"""
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)


def main():
    """メイン関数"""
    app = iTunesToEACGUI()
    app.run()


if __name__ == "__main__":
    main()

