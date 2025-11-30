"""Wikipedia検索モジュール"""

import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import re
import logging

from models.search_result import SearchResult


class WikipediaSearcher:
    """Wikipedia日本語版検索クラス"""
    
    API_URL = 'https://ja.wikipedia.org/w/api.php'
    TIMEOUT = 10
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'iTunes-to-EAC/2.0 (https://github.com/yourproject)'
        })
    
    def search(self, artist: str, album: str) -> List[SearchResult]:
        """
        Wikipediaでアルバム検索
        
        Args:
            artist: アーティスト名
            album: アルバム名
        
        Returns:
            検索結果リスト
        """
        search_query = f"{artist} {album}"
        
        try:
            # ページ検索
            search_results = self._search_pages(search_query)
            
            results = []
            
            for page_info in search_results[:3]:  # 上位3件のみ
                # ページ内容取得
                tracks = self._extract_tracklist(page_info['pageid'])
                
                if tracks:
                    results.append(SearchResult(
                        source='wikipedia',
                        album_title=page_info['title'],
                        tracks=tracks,
                        confidence='high',
                        url=f"https://ja.wikipedia.org/?curid={page_info['pageid']}"
                    ))
            
            return results
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Wikipedia検索エラー: {e}")
            return []
    
    def _search_pages(self, query: str) -> List[Dict]:
        """ページ検索"""
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': 5,
            'utf8': 1
        }
        
        response = self.session.get(
            self.API_URL,
            params=params,
            timeout=self.TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('query', {}).get('search', [])
    
    def _extract_tracklist(self, page_id: int) -> List[Dict]:
        """ページからトラックリスト抽出"""
        params = {
            'action': 'parse',
            'format': 'json',
            'pageid': page_id,
            'prop': 'text'
        }
        
        response = self.session.get(
            self.API_URL,
            params=params,
            timeout=self.TIMEOUT
        )
        
        data = response.json()
        html_content = data['parse']['text']['*']
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # パターン1: <ol>リスト
        tracks = self._extract_from_ol(soup)
        
        # パターン2: テーブル
        if not tracks:
            tracks = self._extract_from_table(soup)
        
        return tracks
    
    def _extract_from_ol(self, soup: BeautifulSoup) -> List[Dict]:
        """<ol>形式からトラック抽出"""
        # "収録曲" セクションを探す
        section = soup.find('span', id=re.compile(r'収録曲|トラック.*リスト'))
        
        if not section:
            return []
        
        ol = section.find_next('ol')
        if not ol:
            return []
        
        tracks = []
        for idx, li in enumerate(ol.find_all('li'), 1):
            text = li.get_text(strip=True)
            
            # "タイトル (原題: Original Title)" 形式を解析
            title_ja = self._parse_japanese_title(text)
            title_en = self._parse_english_title(text)
            
            if title_ja:
                tracks.append({
                    'number': idx,
                    'title_ja': title_ja,
                    'title_en': title_en
                })
        
        return tracks
    
    def _extract_from_table(self, soup: BeautifulSoup) -> List[Dict]:
        """テーブル形式からトラック抽出"""
        table = soup.find('table', class_='tracklist')
        
        if not table:
            return []
        
        tracks = []
        for row in table.find_all('tr')[1:]:  # ヘッダー行スキップ
            cols = row.find_all('td')
            if len(cols) >= 2:
                tracks.append({
                    'number': len(tracks) + 1,
                    'title_ja': cols[1].get_text(strip=True),
                    'title_en': cols[2].get_text(strip=True) if len(cols) > 2 else ''
                })
        
        return tracks
    
    def _parse_japanese_title(self, text: str) -> str:
        """日本語タイトルを抽出"""
        # "タイトル (原題: ...)" または "タイトル - ..." 形式
        match = re.match(r'^([^\(（\-]+)', text)
        return match.group(1).strip() if match else text
    
    def _parse_english_title(self, text: str) -> str:
        """英語タイトル（原題）を抽出"""
        # "... (原題: Original Title)" 形式
        match = re.search(r'\(原題[：:]\s*([^\)）]+)', text)
        return match.group(1).strip() if match else ''

