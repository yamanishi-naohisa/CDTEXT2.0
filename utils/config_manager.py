"""設定管理モジュール"""

import configparser
from pathlib import Path
from typing import Optional


class ConfigManager:
    """設定ファイル管理クラス"""
    
    def __init__(self, config_path: str = "config.ini"):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self.load()
    
    def load(self):
        """設定ファイルを読み込む"""
        if self.config_path.exists():
            self.config.read(self.config_path, encoding='utf-8')
        else:
            # デフォルト設定を作成
            self._create_default_config()
            self.save()
    
    def save(self):
        """設定ファイルを保存"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: Optional[str] = None) -> str:
        """
        設定値を取得
        
        Args:
            section: セクション名
            key: キー名
            fallback: デフォルト値
        
        Returns:
            設定値
        """
        return self.config.get(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """ブール値を取得"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """整数値を取得"""
        return self.config.getint(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: str):
        """設定値を設定"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
    
    def _create_default_config(self):
        """デフォルト設定を作成"""
        # Paths
        self.config.add_section('Paths')
        self.config.set('Paths', 'itunes_path', r'C:\Program Files\iTunes\iTunes.exe')
        self.config.set('Paths', 'eac_path', r'C:\Program Files (x86)\Exact Audio Copy\EAC.exe')
        self.config.set('Paths', 'cdplayer_output', '')
        
        # Options
        self.config.add_section('Options')
        self.config.set('Options', 'itunes_startup_wait', '10')
        self.config.set('Options', 'cd_recognition_wait', '5')
        self.config.set('Options', 'itunes_shutdown_wait', '3')
        self.config.set('Options', 'log_level', 'INFO')
        self.config.set('Options', 'auto_launch_eac', 'true')
        self.config.set('Options', 'play_sound_on_complete', 'true')
        self.config.set('Options', 'restore_last_cd_info', 'false')
        
        # Encoding
        self.config.add_section('Encoding')
        self.config.set('Encoding', 'cdplayer_encoding', 'shift_jis')
        
        # GUI
        self.config.add_section('GUI')
        self.config.set('GUI', 'window_width', '900')
        self.config.set('GUI', 'window_height', '700')
        self.config.set('GUI', 'theme', 'default')
        self.config.set('GUI', 'max_log_lines', '1000')
        
        # WebSearch
        self.config.add_section('WebSearch')
        self.config.set('WebSearch', 'enable_web_search', 'true')
        self.config.set('WebSearch', 'use_wikipedia_ja', 'true')
        self.config.set('WebSearch', 'use_musicbrainz', 'true')
        self.config.set('WebSearch', 'use_general_search', 'false')
        self.config.set('WebSearch', 'search_timeout', '30')
        self.config.set('WebSearch', 'max_candidates', '5')
        self.config.set('WebSearch', 'search_priority', 'wikipedia,musicbrainz,general')
        
        # SearchBehavior
        self.config.add_section('SearchBehavior')
        self.config.set('SearchBehavior', 'auto_apply_mode', 'manual')
        self.config.set('SearchBehavior', 'auto_apply_threshold', '80')
        self.config.set('SearchBehavior', 'warn_low_confidence', 'true')
        self.config.set('SearchBehavior', 'low_confidence_threshold', '60')
        
        # Cache
        self.config.add_section('Cache')
        self.config.set('Cache', 'enable_cache', 'true')
        self.config.set('Cache', 'cache_expire_days', '30')
        self.config.set('Cache', 'max_cache_size_mb', '100')
        self.config.set('Cache', 'cache_dir', 'cache')
        
        # Display
        self.config.add_section('Display')
        self.config.set('Display', 'show_confidence_in_tracklist', 'true')
        self.config.set('Display', 'show_language_indicator', 'true')
        self.config.set('Display', 'preview_max_lines', '10')

