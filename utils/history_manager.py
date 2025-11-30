"""履歴管理モジュール"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from models.cd_info import CDInfo


class HistoryManager:
    """CD処理履歴管理クラス"""
    
    def __init__(self, history_dir: str = "history"):
        """
        初期化
        
        Args:
            history_dir: 履歴ディレクトリ
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        self.history_file = self.history_dir / "history.json"
        self._history: List[Dict] = []
        self.load()
    
    def load(self):
        """履歴を読み込む"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except Exception:
                self._history = []
        else:
            self._history = []
    
    def save(self):
        """履歴を保存"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self._history, f, ensure_ascii=False, indent=2)
    
    def add(self, cd_info: CDInfo, status: str = "success"):
        """
        CD情報を履歴に追加
        
        Args:
            cd_info: CD情報
            status: 処理ステータス
        """
        entry = {
            'date': datetime.now().isoformat(),
            'artist': cd_info.artist,
            'album': cd_info.album,
            'genre': cd_info.genre,
            'year': cd_info.year,
            'tracks_count': cd_info.num_tracks,
            'search_performed': cd_info.search_performed,
            'japanese_titles_obtained': sum(1 for t in cd_info.tracks if t.title_ja),
            'confidence_average': (
                sum(t.confidence_score for t in cd_info.tracks if t.title_ja) /
                max(1, sum(1 for t in cd_info.tracks if t.title_ja))
            ) if any(t.title_ja for t in cd_info.tracks) else 0,
            'status': status,
            'cd_info': cd_info.to_dict()
        }
        
        self._history.append(entry)
        self.save()
    
    def get_all(self) -> List[Dict]:
        """全履歴を取得"""
        return self._history.copy()
    
    def search(self, query: str) -> List[Dict]:
        """
        履歴を検索
        
        Args:
            query: 検索クエリ
        
        Returns:
            検索結果
        """
        query_lower = query.lower()
        results = []
        
        for entry in self._history:
            if (query_lower in entry.get('artist', '').lower() or
                query_lower in entry.get('album', '').lower()):
                results.append(entry)
        
        return results
    
    def get_latest(self, limit: int = 10) -> List[Dict]:
        """
        最新の履歴を取得
        
        Args:
            limit: 取得件数
        
        Returns:
            最新の履歴
        """
        return sorted(
            self._history,
            key=lambda x: x.get('date', ''),
            reverse=True
        )[:limit]
    
    def clear(self):
        """履歴をクリア"""
        self._history = []
        self.save()

