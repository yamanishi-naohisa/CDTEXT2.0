"""EAC制御モジュール"""

import subprocess
import logging
from pathlib import Path
from typing import Optional


class EACController:
    """EAC制御クラス"""
    
    def __init__(self, eac_path: str):
        """
        初期化
        
        Args:
            eac_path: EAC実行ファイルのパス
        """
        self.eac_path = Path(eac_path)
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
    
    def is_available(self) -> bool:
        """EACが利用可能かチェック"""
        return self.eac_path.exists()
    
    def start(self) -> bool:
        """
        EACを起動
        
        Returns:
            成功したかどうか
        """
        if not self.is_available():
            self.logger.error(f"EACが見つかりません: {self.eac_path}")
            return False
        
        try:
            self.process = subprocess.Popen([str(self.eac_path)])
            self.logger.info("EACを起動しました")
            return True
        except Exception as e:
            self.logger.error(f"EAC起動エラー: {e}")
            return False
    
    def is_running(self) -> bool:
        """EACが起動中かチェック"""
        if not self.process:
            return False
        
        return self.process.poll() is None
    
    def stop(self) -> bool:
        """
        EACを終了
        
        Returns:
            成功したかどうか
        """
        if not self.process:
            return True
        
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
            self.logger.info("EACを終了しました")
            return True
        except Exception as e:
            self.logger.error(f"EAC終了エラー: {e}")
            try:
                self.process.kill()
                self.process = None
                return True
            except:
                return False

