import os
from flask import Flask
from dotenv import load_dotenv
from app.routes import main, auth, product, cart, order, review, admin, user, api, mail

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
    
    # ブループリント登録
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
    
    return app 