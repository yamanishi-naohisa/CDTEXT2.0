"""トラック情報データクラス"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    """トラック情報を保持するデータクラス"""
    
    # 基本情報
    number: int = 0
    title: str = ""  # 表示用タイトル（優先順位: title_ja > title_en）
    artist: str = ""
    duration: int = 0  # 秒
    
    # v2.0 新規フィールド
    title_en: str = ""        # 英語タイトル（原題）
    title_ja: Optional[str] = None  # 日本語タイトル
    confidence_score: int = 0  # 信頼度スコア（0-100）
    search_source: Optional[str] = None  # 'wikipedia', 'musicbrainz', etc.
    
    def __post_init__(self):
        """初期化後処理"""
        # title_enが空の場合、titleから設定
        if not self.title_en and self.title:
            self.title_en = self.title
        
        # 表示用タイトルの決定
        self.update_display_title()
    
    def update_display_title(self):
        """表示用タイトルを更新"""
        if self.title_ja:
            self.title = self.title_ja
        else:
            self.title = self.title_en
    
    def set_japanese_title(self, title_ja: str, source: str, confidence: int):
        """日本語タイトルを設定"""
        self.title_ja = title_ja
        self.search_source = source
        self.confidence_score = confidence
        self.update_display_title()
    
    def clear_japanese_title(self):
        """日本語タイトルをクリア（原題に戻す）"""
        self.title_ja = None
        self.search_source = None
        self.confidence_score = 0
        self.update_display_title()
    
    def get_confidence_level(self) -> str:
        """信頼度レベルを取得"""
        if self.confidence_score >= 80:
            return 'high'
        elif self.confidence_score >= 60:
            return 'medium'
        elif self.confidence_score >= 40:
            return 'low'
        else:
            return 'unknown'
    
    def get_confidence_stars(self) -> str:
        """信頼度を星で表示"""
        level = self.get_confidence_level()
        stars = {
            'high': '★★★',
            'medium': '★★',
            'low': '★',
            'unknown': '[?]'
        }
        return stars.get(level, '[?]')
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'number': self.number,
            'title': self.title,
            'title_en': self.title_en,
            'title_ja': self.title_ja,
            'artist': self.artist,
            'duration': self.duration,
            'confidence_score': self.confidence_score,
            'search_source': self.search_source
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Track':
        """辞書から復元"""
        return cls(
            number=data.get('number', 0),
            title=data.get('title', ''),
            title_en=data.get('title_en', ''),
            title_ja=data.get('title_ja'),
            artist=data.get('artist', ''),
            duration=data.get('duration', 0),
            confidence_score=data.get('confidence_score', 0),
            search_source=data.get('search_source')
        )

