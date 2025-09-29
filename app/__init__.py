import os
from flask import Flask, jsonify
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # 本番環境とローカル環境の設定を分ける
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'vulnerable_shop_secret_key_12345')
    
    # 本番環境での設定
    if os.getenv('FLASK_ENV') == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
    else:
        app.config['DEBUG'] = True
    
    # ヘルスチェックエンドポイント（デバッグ用に残す）
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'OK',
            'message': 'Application is running',
            'environment': os.getenv('FLASK_ENV', 'development'),
            'database': 'PostgreSQL' if os.getenv('DATABASE_URL') else 'SQLite',
            'supabase_configured': bool(os.getenv('SUPABASE_URL')),
            'env_variables': {
                'SUPABASE_URL': '✅' if os.getenv('SUPABASE_URL') else '❌',
                'SUPABASE_KEY': '✅' if os.getenv('SUPABASE_KEY') else '❌',
                'DATABASE_URL': '✅' if os.getenv('DATABASE_URL') else '❌',
                'FLASK_SECRET_KEY': '✅' if os.getenv('FLASK_SECRET_KEY') else '❌'
            }
        })
        
    # データベース接続テスト用エンドポイント
    @app.route('/db-test')
    def db_test():
        try:
            from app.database import db_config
            # 簡単なクエリでテスト
            result = db_config.execute_query("SELECT 1 as test")
            return jsonify({
                'database_connection': 'Success',
                'query_result': result,
                'connection_type': 'PostgreSQL' if db_config.use_postgres else 'SQLite'
            })
        except Exception as e:
            return jsonify({
                'database_connection': 'Failed',
                'error': str(e)
            }), 500
    
    # エラーハンドラー
    @app.errorhandler(500)
    def internal_error(error):
        if os.getenv('FLASK_ENV') == 'production':
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'サーバーエラーが発生しました'
            }), 500
        else:
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(error)
            }), 500
    
    # ブループリント登録
    try:
        from app.routes import main, auth, product, cart, order, review, admin, user, api, mail
        
        app.register_blueprint(main.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(product.bp)
        app.register_blueprint(cart.bp)
        app.register_blueprint(order.bp)
        app.register_blueprint(review.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(user.bp)
        app.register_blueprint(api.bp)
        app.register_blueprint(mail.bp)
        
        print("✅ 全ブループリント登録完了")
        
    except ImportError as e:
        print(f"❌ ブループリント登録エラー: {e}")
        
        # フォールバック: 基本的なルートのみ
        @app.route('/')
        def fallback_index():
            return jsonify({
                'message': '🔒 脆弱なショッピングモール - ウェブセキュリティ演習サイト',
                'status': 'running (fallback mode)',
                'note': '⚠️ このサイトは学習目的のみで使用してください',
                'error': 'Some modules failed to load',
                'debug': 'テンプレートまたはデータベース接続の問題が発生しました'
            })
    
    return app 