"""検索結果データクラス"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

from .cd_info import CDInfo


@dataclass
class SearchResult:
    """Web検索結果を保持するデータクラス"""
    
    source: str  # 'wikipedia', 'musicbrainz', 'general'
    album_title: str
    tracks: List[dict]  # {'number': int, 'title_ja': str, 'title_en': str}
    confidence: str  # 'high', 'medium', 'low'
    url: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def calculate_match_score(self, cd_info: CDInfo) -> float:
        """CD情報とのマッチングスコア計算"""
        from difflib import SequenceMatcher
        
        # アルバム名の類似度
        album_similarity = SequenceMatcher(
            None,
            cd_info.album.lower(),
            self.album_title.lower()
        ).ratio()
        
        # トラック数の一致
        track_count_match = 1.0 if len(self.tracks) == cd_info.num_tracks else 0.5
        
        # 総合スコア
        return (album_similarity * 0.6 + track_count_match * 0.4) * 100

