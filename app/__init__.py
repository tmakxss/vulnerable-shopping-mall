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
            'database': 'Connected' if os.getenv('DATABASE_URL') else 'Local SQLite'
        })
    
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
                'error': 'Some modules failed to load'
            })
    
    return app 