# Vercel Serverless Function Entry Point
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

# Vercel用のアプリケーションインスタンス
app = create_app()

# Vercel Functions用のハンドラー
def handler(request):
    return app(request.environ, request.start_response)

# デバッグ情報出力
if __name__ == "__main__":
    print("🔍 Vercel API Handler初期化")
    print(f"🔍 Python Path: {sys.path}")
    print("🚀 アプリケーション準備完了")