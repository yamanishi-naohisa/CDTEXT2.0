"""Web検索統合管理モジュール"""

from typing import List, Optional, Callable
import logging

from models.cd_info import CDInfo
from models.search_result import SearchResult
from .wikipedia_searcher import WikipediaSearcher
from .musicbrainz_searcher import MusicBrainzSearcher
from .matcher import TrackMatcher
from .confidence_scorer import ConfidenceScorer
from .cache_manager import CacheManager


class WebSearchManager:
    """Web検索統合管理クラス"""
    
    def __init__(self, config: dict):
        """
        初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 検索エンジン初期化
        self.searchers = []
        
        if config.get('use_wikipedia_ja', True):
            self.searchers.append(WikipediaSearcher())
        
        if config.get('use_musicbrainz', True):
            self.searchers.append(MusicBrainzSearcher())
        
        # キャッシュ管理
        self.cache = CacheManager(
            cache_dir=config.get('cache_dir', 'cache'),
            expire_days=config.get('cache_expire_days', 30)
        )
        
        # マッチャー
        self.matcher = TrackMatcher()
        
        # 信頼度評価
        self.scorer = ConfidenceScorer()
    
    def search_titles(self, cd_info: CDInfo,
                     force_refresh: bool = False,
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> List[SearchResult]:
        """
        CD情報から邦題を検索
        
        Args:
            cd_info: CD情報
            force_refresh: キャッシュを無視して強制検索
            progress_callback: 進行状況コールバック関数(current, total)
        
        Returns:
            検索結果リスト
        """
        # キャッシュ確認
        if not force_refresh and self.config.get('enable_cache', True):
            cached = self.cache.get(cd_info.artist, cd_info.album)
            if cached:
                self.logger.info("キャッシュから検索結果を読み込み")
                return [SearchResult(**r) for r in cached]
        
        # 検索実行
        all_results = []
        
        for idx, searcher in enumerate(self.searchers):
            try:
                self.logger.info(f"{searcher.__class__.__name__}で検索中...")
                
                results = searcher.search(cd_info.artist, cd_info.album)
                all_results.extend(results)
                
                if progress_callback:
                    progress_callback(idx + 1, len(self.searchers))
                
            except Exception as e:
                self.logger.error(f"検索エラー ({searcher.__class__.__name__}): {e}")
        
        # キャッシュ保存
        if all_results and self.config.get('enable_cache', True):
            cache_data = [r.__dict__ for r in all_results]
            self.cache.set(cd_info.artist, cd_info.album, cache_data)
        
        return all_results
    
    def apply_search_results(self, cd_info: CDInfo,
                            search_results: List[SearchResult],
                            auto_apply: bool = False,
                            threshold: int = 80) -> CDInfo:
        """
        検索結果をCD情報に適用
        
        Args:
            cd_info: CD情報
            search_results: 検索結果
            auto_apply: 自動適用モード
            threshold: 自動適用の信頼度閾値
        
        Returns:
            更新されたCD情報
        """
        # トラックマッチング
        matched_tracks = self.matcher.match_tracks(
            cd_info.tracks,
            search_results
        )
        
        # 各トラックに適用
        for original_track, match_result in zip(cd_info.tracks, matched_tracks):
            if not match_result:
                continue
            
            # 信頼度スコア計算
            confidence = self.scorer.calculate_score(match_result)
            
            # 自動適用判定
            if auto_apply and confidence >= threshold:
                original_track.set_japanese_title(
                    match_result['matched']['title_ja'],
                    match_result['source'],
                    confidence
                )
                self.logger.info(
                    f"トラック{original_track.number}: "
                    f"自動適用 (信頼度: {confidence})"
                )
        
        cd_info.search_performed = True
        cd_info.language = cd_info.detect_language()
        
        return cd_info

