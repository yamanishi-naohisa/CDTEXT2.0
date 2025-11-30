"""トラックマッチングモジュール"""

from difflib import SequenceMatcher
from typing import List, Optional, Dict

from models.track import Track
from models.search_result import SearchResult


class TrackMatcher:
    """トラックマッチングクラス"""
    
    SIMILARITY_THRESHOLD = 0.7
    
    def match_tracks(self, original_tracks: List[Track],
                    search_results: List[SearchResult]) -> List[Optional[Dict]]:
        """
        オリジナルトラックと検索結果をマッチング
        
        Args:
            original_tracks: オリジナルのトラックリスト
            search_results: 検索結果リスト
        
        Returns:
            マッチング結果リスト（各トラックに対応）
        """
        matched = []
        
        for orig_track in original_tracks:
            best_match = None
            best_score = 0
            
            for result in search_results:
                for result_track in result.tracks:
                    # マッチングスコア計算
                    score = self._calculate_similarity(
                        orig_track,
                        result_track,
                        result
                    )
                    
                    if score > best_score and score > self.SIMILARITY_THRESHOLD:
                        best_score = score
                        best_match = {
                            'original': orig_track,
                            'matched': result_track,
                            'similarity': score,
                            'source': result.source,
                            'confidence': result.confidence
                        }
            
            matched.append(best_match)
        
        return matched
    
    def _calculate_similarity(self, orig_track: Track,
                                result_track: Dict,
                                result: SearchResult) -> float:
        """
        トラック類似度計算
        
        Returns:
            類似度スコア（0.0-1.0）
        """
        # 英語タイトルで比較
        orig_title = orig_track.title_en.lower()
        result_title = result_track.get('title_en', '').lower()
        
        # 文字列類似度
        title_similarity = SequenceMatcher(
            None,
            orig_title,
            result_title
        ).ratio()
        
        # トラック番号の一致度
        number_match = 1.0 if orig_track.number == result_track.get('number', 0) else 0.5
        
        # 総合スコア
        return title_similarity * 0.7 + number_match * 0.3

