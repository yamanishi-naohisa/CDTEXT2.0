"""CDPLAYER.INI生成モジュール"""

import os
import logging
from pathlib import Path
from typing import Optional

from models.cd_info import CDInfo


class CDPlayerGenerator:
    """CDPLAYER.INI生成クラス"""
    
    def __init__(self, encoding: str = "shift_jis"):
        """
        初期化
        
        Args:
            encoding: 出力エンコーディング
        """
        self.encoding = encoding
        self.logger = logging.getLogger(__name__)
    
    def generate(self, cd_info: CDInfo, output_path: Optional[str] = None) -> bool:
        """
        CDPLAYER.INIファイルを生成
        
        Args:
            cd_info: CD情報
            output_path: 出力先パス（Noneの場合は%USERPROFILE%\CDPLAYER.INI）
        
        Returns:
            成功したかどうか
        """
        if output_path:
            output_file = Path(output_path)
        else:
            # デフォルトはユーザーディレクトリ
            output_file = Path(os.path.expanduser("~")) / "CDPLAYER.INI"
        
        try:
            # エンコーディング設定
            if self.encoding == "utf-8-sig":
                # UTF-8 BOM付き
                encoding = "utf-8-sig"
            elif self.encoding == "shift_jis":
                encoding = "shift_jis"
            else:
                encoding = "utf-8"
            
            with open(output_file, 'w', encoding=encoding) as f:
                # アルバム情報
                f.write(f"[{cd_info.album}]\n")
                f.write(f"ARTIST={cd_info.artist}\n")
                f.write(f"ALBUM={cd_info.album}\n")
                if cd_info.genre:
                    f.write(f"GENRE={cd_info.genre}\n")
                if cd_info.year:
                    f.write(f"YEAR={cd_info.year}\n")
                f.write("\n")
                
                # トラック情報
                for track in cd_info.tracks:
                    # 日本語タイトルがあればそれを使用、なければ原題
                    title = track.title_ja if track.title_ja else track.title_en
                    
                    f.write(f"TITLE{track.number:02d}={title}\n")
                    if track.artist and track.artist != cd_info.artist:
                        f.write(f"ARTIST{track.number:02d}={track.artist}\n")
                
                f.write("\n")
            
            self.logger.info(f"CDPLAYER.INIを作成しました: {output_file}")
            self.logger.info(f"日本語タイトル: {sum(1 for t in cd_info.tracks if t.title_ja)}/{len(cd_info.tracks)}件適用")
            return True
        
        except Exception as e:
            self.logger.error(f"CDPLAYER.INI生成エラー: {e}")
            return False

