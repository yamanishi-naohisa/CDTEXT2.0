"""ログシステムモジュール"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "itunes_to_eac", log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    ロガーをセットアップ
    
    Args:
        name: ロガー名
        log_level: ログレベル
        log_dir: ログディレクトリ
    
    Returns:
        設定済みロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 既存のハンドラをクリア
    logger.handlers.clear()
    
    # ログディレクトリ作成
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # ファイルハンドラ
    log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "itunes_to_eac") -> logging.Logger:
    """
    ロガーを取得（既にセットアップされている場合）
    
    Args:
        name: ロガー名
    
    Returns:
        ロガー
    """
    return logging.getLogger(name)

