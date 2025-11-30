"""MusicBrainz検索モジュール"""

from typing import List, Optional, Dict
import logging

try:
    import musicbrainzngs
    MUSICBRAINZ_AVAILABLE = True
except ImportError:
    MUSICBRAINZ_AVAILABLE = False

from models.search_result import SearchResult


class MusicBrainzSearcher:
    """MusicBrainz検索クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if not MUSICBRAINZ_AVAILABLE:
            self.logger.warning("musicbrainzngsがインストールされていません")
            return
        
        # MusicBrainz初期化
        musicbrainzngs.set_useragent(
            "iTunes-to-EAC",
            "2.0",
            "https://github.com/yourproject"
        )
        musicbrainzngs.set_rate_limit(limit_or_interval=1.0)
    
    def search(self, artist: str, album: str) -> List[SearchResult]:
        """
        MusicBrainzでアルバム検索
        
        Args:
            artist: アーティスト名
            album: アルバム名
        
        Returns:
            検索結果リスト
        """
        if not MUSICBRAINZ_AVAILABLE:
            return []
        
        try:
            # リリース検索
            result = musicbrainzngs.search_releases(
                artist=artist,
                release=album,
                limit=5
            )
            
            results = []
            
            for release in result['release-list']:
                release_id = release['id']
                
                # 詳細情報取得
                tracks = self._get_release_tracks(release_id)
                
                # 日本語タイトルが1つでもあれば結果に追加
                if any(t['title_ja'] for t in tracks):
                    results.append(SearchResult(
                        source='musicbrainz',
                        album_title=release['title'],
                        tracks=tracks,
                        confidence='medium',
                        metadata={'mbid': release_id}
                    ))
            
            return results
        
        except Exception as e:
            self.logger.error(f"MusicBrainz検索エラー: {e}")
            return []
    
    def _get_release_tracks(self, release_id: str) -> List[Dict]:
        """リリースのトラック情報取得"""
        try:
            release_detail = musicbrainzngs.get_release_by_id(
                release_id,
                includes=['recordings', 'artist-credits']
            )
            
            tracks = []
            medium_list = release_detail['release'].get('medium-list', [])
            
            for medium in medium_list:
                for track in medium.get('track-list', []):
                    recording = track['recording']
                    
                    # 日本語エイリアス検索
                    ja_title = self._find_japanese_alias(recording)
                    
                    tracks.append({
                        'number': int(track['position']),
                        'title_ja': ja_title,
                        'title_en': recording['title']
                    })
            
            return tracks
        
        except Exception as e:
            self.logger.error(f"リリース詳細取得エラー: {e}")
            return []
    
    def _find_japanese_alias(self, recording: Dict) -> Optional[str]:
        """レコーディングの日本語エイリアスを検索"""
        aliases = recording.get('alias-list', [])
        
        for alias in aliases:
            if alias.get('locale') == 'ja':
                return alias['name']
        
        return None

