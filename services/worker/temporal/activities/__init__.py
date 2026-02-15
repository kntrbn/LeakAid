# Activities パッケージ
# 全てのアクティビティを自動的に export

import importlib
import pkgutil
from pathlib import Path

__all__ = []

# 現在のディレクトリの全ての .py ファイルからアクティビティを自動インポート
current_dir = Path(__file__).parent
for _, module_name, _ in pkgutil.iter_modules([str(current_dir)]):
    if module_name.startswith("_"):
        continue
    
    module = importlib.import_module(f".{module_name}", package=__name__)
    
    # モジュール内の全ての関数/クラスを取得
    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        attr = getattr(module, attr_name)
        # アクティビティ関数/クラスを判定
        if callable(attr) and hasattr(attr, "__temporal_activity_definition"):
            globals()[attr_name] = attr
            __all__.append(attr_name)