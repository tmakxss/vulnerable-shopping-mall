import os
from app import create_app

# Vercel環境でのデバッグ情報
print(f"🔍 Python実行環境: {os.getcwd()}")
print(f"🔍 FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"🔍 環境変数確認:")
for key in ['SUPABASE_URL', 'SUPABASE_KEY', 'DATABASE_URL', 'FLASK_SECRET_KEY']:
    value = os.getenv(key)
    print(f"   {key}: {'✅' if value else '❌'} ({len(value) if value else 0} chars)")

# アプリケーション作成
app = create_app()

# Vercel用: アプリケーション設定を追加
print("🚀 Vercelでアプリケーション初期化完了")

# ヘルスチェック用追加エンドポイント
@app.route('/ping')
def ping():
    return {'status': 'ok', 'message': 'Vercel deployment successful'}

if __name__ == '__main__':
    print("🔒 脆弱なショッピングモール - ウェブセキュリティ演習サイト")
    print("🌐 サーバー起動中... http://localhost:5000")
    print("⚠️  このサイトは学習目的のみで使用してください")
    
    # ローカル開発時のみデバッグモード
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 