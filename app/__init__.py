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
    
    # 商品データ直接取得エンドポイント
    @app.route('/api/products')
    def api_products():
        try:
            from app.database import db_config
            
            # 接続状況をログ出力
            print(f"🔍 PostgreSQL使用: {db_config.use_postgres}")
            print(f"🔍 DATABASE_URL設定済み: {bool(os.getenv('DATABASE_URL'))}")
            
            # まずテーブルの存在確認
            table_check = db_config.execute_query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'products'
            """)
            
            if not table_check:
                return jsonify({
                    'success': False,
                    'error': 'products table not found',
                    'debug': 'テーブルが作成されていません'
                })
            
            # 商品数をカウント
            count_result = db_config.execute_query("SELECT COUNT(*) as count FROM products")
            product_count = count_result[0]['count'] if count_result else 0
            
            # 商品データを取得
            products = db_config.execute_query("SELECT * FROM products LIMIT 10")
            
            return jsonify({
                'success': True,
                'table_exists': True,
                'total_products': product_count,
                'fetched_count': len(products),
                'products': products,
                'connection_type': 'PostgreSQL' if db_config.use_postgres else 'SQLite'
            })
            
        except Exception as e:
            print(f"❌ API商品取得エラー: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }), 500
    
    # ユーザーデータ直接取得エンドポイント  
    @app.route('/api/users')
    def api_users():
        try:
            from app.database import db_config
            
            # テーブル存在確認
            table_check = db_config.execute_query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            """)
            
            if not table_check:
                return jsonify({
                    'success': False,
                    'error': 'users table not found',
                    'debug': 'ユーザーテーブルが作成されていません'
                })
            
            # ユーザー数をカウント
            count_result = db_config.execute_query("SELECT COUNT(*) as count FROM users")
            user_count = count_result[0]['count'] if count_result else 0
            
            # ユーザーデータを取得
            users = db_config.execute_query("SELECT id, username, email, is_admin FROM users")
            
            return jsonify({
                'success': True,
                'table_exists': True,
                'total_users': user_count,
                'fetched_count': len(users),
                'users': users
            })
            
        except Exception as e:
            print(f"❌ APIユーザー取得エラー: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }), 500
    
    # 全テーブル一覧確認エンドポイント
    @app.route('/api/tables')
    def api_tables():
        try:
            from app.database import db_config
            
            tables = db_config.execute_query("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            return jsonify({
                'success': True,
                'database_type': 'PostgreSQL' if db_config.use_postgres else 'SQLite',
                'tables': tables
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # 緊急用: テーブル作成エンドポイント
    @app.route('/api/create-tables')
    def create_tables():
        try:
            from app.database import db_config
            
            # ユーザーテーブル作成
            db_config.execute_update("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    address TEXT,
                    phone VARCHAR(255),
                    is_admin BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 商品テーブル作成
            db_config.execute_update("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    stock INTEGER DEFAULT 0,
                    category VARCHAR(255),
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # レビューテーブル作成
            db_config.execute_update("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            return jsonify({
                'success': True,
                'message': 'テーブル作成完了'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # 緊急用: 初期データ投入エンドポイント
    @app.route('/api/seed-data')
    def seed_data():
        try:
            from app.database import db_config
            
            # テストユーザー作成
            db_config.execute_update("""
                INSERT INTO users (username, password, email, is_admin) VALUES 
                ('admin', 'admin123', 'admin@shop.com', true),
                ('user1', 'password123', 'user1@test.com', false)
                ON CONFLICT (username) DO NOTHING
            """)
            
            # テスト商品作成
            db_config.execute_update("""
                INSERT INTO products (name, description, price, stock, category, image_url) VALUES 
                ('ノートパソコン', '高性能ノートパソコンです', 120000.00, 10, '電子機器', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop'),
                ('スマートフォン', '最新スマートフォンです', 80000.00, 15, '電子機器', 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop'),
                ('ヘッドフォン', '高音質ヘッドフォンです', 15000.00, 20, '電子機器', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop')
            """)
            
            return jsonify({
                'success': True,
                'message': '初期データ投入完了'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
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