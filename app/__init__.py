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
    
    # テスト用エンドポイント
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'OK',
            'message': 'Application is running',
            'environment': os.getenv('FLASK_ENV', 'development')
        })
    
    @app.route('/')
    def index():
        return jsonify({
            'message': '🔒 脆弱なショッピングモール - ウェブセキュリティ演習サイト',
            'status': 'running',
            'note': '⚠️ このサイトは学習目的のみで使用してください'
        })
    
    # エラーハンドラー
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error)
        }), 500
    
    try:
        # ブループリント登録（エラーが発生した場合はスキップ）
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
        
    except Exception as e:
        print(f"ブループリント登録エラー: {e}")
        # 基本的なルートのみで起動
    
    return app 