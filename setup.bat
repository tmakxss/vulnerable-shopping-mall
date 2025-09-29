@echo off
REM Vulnerable Shopping Mall - Quick Setup Script (Windows)
echo 🔒 脆弱なショッピングモール セットアップ開始
echo ⚠️  このサイトは学習目的のみで使用してください
echo.

REM 仮想環境の作成
echo 📦 仮想環境を作成中...
python -m venv venv

REM 仮想環境のアクティベート (Windows)
echo 🔄 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

REM 依存関係のインストール
echo 📚 依存関係をインストール中...
pip install -r requirements.txt

REM データベースの初期化
echo 🗄️  データベースを初期化中...
python database\init_db.py

echo.
echo ✅ セットアップ完了！
echo.
echo 🚀 サーバーを起動するには:
echo    python run.py
echo.
echo 🌐 ブラウザで以下のURLにアクセス:
echo    http://localhost:5000
echo.
echo 👥 テスト用アカウント:
echo    管理者: admin / admin123
echo    ユーザー: user1 / password123
echo.
echo 📖 詳細なデプロイメント手順:
echo    DEPLOYMENT.md を参照してください

pause