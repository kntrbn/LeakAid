# Workflows パッケージ
# 全てのワークフローを自動的に export

import importlib
import pkgutil
from pathlib import Path

__all__ = []

# 現在のディレクトリの全ての .py ファイルからワークフローを自動インポート
current_dir = Path(__file__).parent
for _, module_name, _ in pkgutil.iter_modules([str(current_dir)]):
    if module_name.startswith("_"):
        continue
    
    module = importlib.import_module(f".{module_name}", package=__name__)
    
    # モジュール内の全てのクラスを取得
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        # Workflow クラスを判定（@workflow.defn で装飾されたクラス）
        if isinstance(attr, type) and attr_name.endswith("Workflow"):
            globals()[attr_name] = attr
            __all__.append(attr_name)
