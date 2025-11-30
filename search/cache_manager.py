"""キャッシュ管理モジュール"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict


class CacheManager:
    """検索結果キャッシュ管理クラス"""
    
    def __init__(self, cache_dir: str = 'cache', expire_days: int = 30):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
            expire_days: 有効期限（日）
        """
        self.cache_dir = Path(cache_dir) / 'search_results'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expire_days = expire_days
        self.logger = logging.getLogger(__name__)
    
    def get_cache_key(self, artist: str, album: str) -> str:
        """キャッシュキー生成"""
        key_str = f"{artist.lower()}_{album.lower()}"
        hash_str = hashlib.md5(key_str.encode()).hexdigest()[:8]
        return f"{artist}_{album}_{hash_str}.json"
    
    def get(self, artist: str, album: str) -> Optional[List[Dict]]:
        """
        キャッシュ取得
        
        Args:
            artist: アーティスト名
            album: アルバム名
        
        Returns:
            キャッシュされた検索結果、存在しない場合はNone
        """
        cache_file = self.cache_dir / self.get_cache_key(artist, album)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 有効期限チェック
            search_date_str = data.get('query', {}).get('search_date')
            if search_date_str:
                search_date = datetime.fromisoformat(search_date_str)
                if datetime.now() - search_date > timedelta(days=self.expire_days):
                    self.logger.info("キャッシュが期限切れです")
                    return None
            
            return data.get('results', [])
        
        except Exception as e:
            self.logger.error(f"キャッシュ読み込みエラー: {e}")
            return None
    
    def set(self, artist: str, album: str, results: List[Dict]):
        """
        キャッシュ保存
        
        Args:
            artist: アーティスト名
            album: アルバム名
            results: 検索結果
        """
        cache_file = self.cache_dir / self.get_cache_key(artist, album)
        
        try:
            data = {
                'query': {
                    'artist': artist,
                    'album': album,
                    'search_date': datetime.now().isoformat()
                },
                'results': results,
                'cache_version': '2.0'
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"キャッシュを保存しました: {cache_file.name}")
        
        except Exception as e:
            self.logger.error(f"キャッシュ保存エラー: {e}")
    
    def clear_all(self):
        """全キャッシュ削除"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            self.logger.info("全キャッシュを削除しました")
        except Exception as e:
            self.logger.error(f"キャッシュ削除エラー: {e}")
    
    def get_cache_size(self) -> float:
        """
        キャッシュサイズ取得（MB）
        
        Returns:
            キャッシュサイズ（MB）
        """
        total_size = 0
        for cache_file in self.cache_dir.glob('*.json'):
            total_size += cache_file.stat().st_size
        return total_size / (1024 * 1024)  # MB単位

