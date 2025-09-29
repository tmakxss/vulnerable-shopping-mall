#!/bin/bash

# Vulnerable Shopping Mall - Quick Setup Script
echo "🔒 脆弱なショッピングモール セットアップ開始"
echo "⚠️  このサイトは学習目的のみで使用してください"

# 仮想環境の作成
echo "📦 仮想環境を作成中..."
python -m venv venv

# 仮想環境のアクティベート（Linux/Mac）
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    source venv/bin/activate
    echo "✅ 仮想環境をアクティベートしました (Linux/Mac)"
fi

# 依存関係のインストール
echo "📚 依存関係をインストール中..."
pip install -r requirements.txt

# データベースの初期化
echo "🗄️  データベースを初期化中..."
python database/init_db.py

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "🚀 サーバーを起動するには:"
echo "   python run.py"
echo ""
echo "🌐 ブラウザで以下のURLにアクセス:"
echo "   http://localhost:5000"
echo ""
echo "👥 テスト用アカウント:"
echo "   管理者: admin / admin123"
echo "   ユーザー: user1 / password123"
echo ""
echo "📖 詳細なデプロイメント手順:"
echo "   DEPLOYMENT.md を参照してください"