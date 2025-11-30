"""CD情報データクラス"""

from dataclasses import dataclass, field
from typing import List, Optional
import re

from .track import Track


@dataclass
class CDInfo:
    """CD情報を保持するデータクラス"""
    
    # 基本情報
    artist: str = ""
    album: str = ""
    genre: str = ""
    year: str = ""
    num_tracks: int = 0
    
    # トラック情報
    tracks: List[Track] = field(default_factory=list)
    
    # v2.0 新規フィールド
    language: str = "en"  # 'en', 'ja', 'mixed'
    search_performed: bool = False
    search_timestamp: Optional[str] = None
    
    def __post_init__(self):
        """初期化後処理"""
        if self.tracks:
            self.num_tracks = len(self.tracks)
    
    def detect_language(self) -> str:
        """言語自動判定"""
        japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]'
        
        ja_count = 0
        en_count = 0
        
        for track in self.tracks:
            if re.search(japanese_pattern, track.title):
                ja_count += 1
            else:
                en_count += 1
        
        if ja_count == 0:
            return 'en'
        elif en_count == 0:
            return 'ja'
        else:
            return 'mixed'
    
    def get_japanese_title_ratio(self) -> float:
        """日本語タイトル取得率"""
        if not self.tracks:
            return 0.0
        
        ja_count = sum(1 for t in self.tracks if t.title_ja)
        return ja_count / len(self.tracks)
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'artist': self.artist,
            'album': self.album,
            'genre': self.genre,
            'year': self.year,
            'num_tracks': self.num_tracks,
            'language': self.language,
            'search_performed': self.search_performed,
            'tracks': [track.to_dict() for track in self.tracks]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CDInfo':
        """辞書から復元"""
        tracks = [Track.from_dict(t) for t in data.get('tracks', [])]
        return cls(
            artist=data.get('artist', ''),
            album=data.get('album', ''),
            genre=data.get('genre', ''),
            year=data.get('year', ''),
            num_tracks=data.get('num_tracks', 0),
            tracks=tracks,
            language=data.get('language', 'en'),
            search_performed=data.get('search_performed', False)
        )

