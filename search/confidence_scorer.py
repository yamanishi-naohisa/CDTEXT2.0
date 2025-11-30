"""信頼度スコアリングモジュール"""

from typing import Dict


class ConfidenceScorer:
    """信頼度スコアリングクラス"""
    
    def calculate_score(self, match_result: Dict) -> int:
        """
        マッチング結果から信頼度スコアを計算
        
        Args:
            match_result: マッチング結果
        
        Returns:
            信頼度スコア（0-100）
        """
        score = 0
        
        # 1. 文字列類似度（最大40点）
        similarity = match_result['similarity']
        score += similarity * 40
        
        # 2. トラック番号一致（20点）
        if match_result['original'].number == match_result['matched']['number']:
            score += 20
        
        # 3. ソース信頼性（20点）
        source_scores = {
            'wikipedia': 20,
            'musicbrainz': 15,
            'general': 10
        }
        score += source_scores.get(match_result['source'], 5)
        
        # 4. タイトル完全一致ボーナス（10点）
        if similarity > 0.95:
            score += 10
        
        # 5. 日本語タイトルの存在（10点）
        if match_result['matched'].get('title_ja'):
            score += 10
        
        return min(100, int(score))

