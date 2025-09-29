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
        
    # データベース接続テスト用エンドポイント（詳細版）
    @app.route('/db-test')
    def db_test():
        try:
            from app.database import db_config
            
            results = {}
            
            # 基本接続テスト
            try:
                result = db_config.execute_query("SELECT 1 as test")
                results['basic_query'] = {'success': True, 'result': result}
            except Exception as e:
                results['basic_query'] = {'success': False, 'error': str(e)}
            
            # 個別のクエリで詳細情報を取得
            queries = {
                'current_database': "SELECT current_database()",
                'current_schema': "SELECT current_schema()", 
                'current_user': "SELECT current_user",
                'session_user': "SELECT session_user",
                'postgres_version': "SELECT version()"
            }
            
            for name, query in queries.items():
                try:
                    result = db_config.execute_query(query)
                    results[name] = result[0] if result else None
                except Exception as e:
                    results[name] = f'ERROR: {str(e)}'
            
            # 権限チェック
            try:
                permission_test = db_config.execute_query("""
                    SELECT 
                        has_database_privilege(current_database(), 'CREATE') as can_create,
                        has_schema_privilege('public', 'CREATE') as can_create_in_public
                """)
                results['permissions'] = permission_test[0] if permission_test else None
            except Exception as e:
                results['permissions'] = f'ERROR: {str(e)}'
            
            return jsonify({
                'database_connection': 'Success',
                'connection_type': 'PostgreSQL' if db_config.use_postgres else 'SQLite',
                'database_url_configured': bool(os.getenv('DATABASE_URL')),
                'detailed_results': results
            })
            
        except Exception as e:
            return jsonify({
                'database_connection': 'Failed',
                'error': str(e),
                'error_type': type(e).__name__
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
    
    # 全テーブル一覧確認エンドポイント（詳細診断版）
    @app.route('/api/tables')
    def api_tables():
        try:
            from app.database import db_config
            
            # 全スキーマのテーブルを検索
            all_tables = db_config.execute_query("""
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables 
                WHERE table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """)
            
            # publicスキーマのテーブルのみ
            public_tables = db_config.execute_query("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            # 現在のスキーマを確認
            current_schema = db_config.execute_query("SELECT current_schema()")
            
            # データベース名を確認
            current_db = db_config.execute_query("SELECT current_database()")
            
            return jsonify({
                'success': True,
                'database_type': 'PostgreSQL' if db_config.use_postgres else 'SQLite',
                'current_database': current_db[0] if current_db else None,
                'current_schema': current_schema[0] if current_schema else None,
                'public_tables': public_tables,
                'all_tables': all_tables,
                'total_tables': len(all_tables)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }), 500
    
    # 緊急用: テーブル作成エンドポイント
    @app.route('/api/create-tables')
    def create_tables():
        try:
            from app.database import db_config
            
            results = {}
            
            # 接続テスト
            try:
                test_result = db_config.execute_query("SELECT 1 as test")
                results['connection_test'] = f'SUCCESS: {test_result}'
            except Exception as e:
                results['connection_test'] = f'FAILED: {str(e)}'
            
            # ユーザーテーブル作成
            try:
                print("🔧 ユーザーテーブル作成中...")
                result = db_config.execute_update("""
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
                results['users'] = 'SUCCESS' if result is not None else 'FAILED'
                print(f"✅ ユーザーテーブル作成結果: {results['users']}")
            except Exception as e:
                error_msg = str(e)
                results['users'] = f'ERROR: {error_msg}'
                print(f"❌ ユーザーテーブル作成エラー: {error_msg}")
            
            # 商品テーブル作成
            try:
                result = db_config.execute_update("""
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
                results['products'] = 'SUCCESS' if result is not None else 'FAILED'
            except Exception as e:
                results['products'] = f'ERROR: {str(e)}'
            
            # レビューテーブル作成
            try:
                result = db_config.execute_update("""
                    CREATE TABLE IF NOT EXISTS reviews (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                results['reviews'] = 'SUCCESS' if result is not None else 'FAILED'
            except Exception as e:
                results['reviews'] = f'ERROR: {str(e)}'
            
            success_count = sum(1 for v in results.values() if v == 'SUCCESS')
            
            return jsonify({
                'success': success_count > 0,
                'message': f'{success_count}/3 テーブル作成完了',
                'details': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'message': '全般的なエラー'
            }), 500
    
    # 緊急用: 初期データ投入エンドポイント
    @app.route('/api/seed-data')
    def seed_data():
        try:
            from app.database import db_config
            
            results = {}
            
            # テストユーザー作成
            try:
                result = db_config.execute_update("""
                    INSERT INTO users (username, password, email, is_admin) VALUES 
                    ('admin', 'admin123', 'admin@shop.com', true),
                    ('user1', 'password123', 'user1@test.com', false)
                    ON CONFLICT (username) DO NOTHING
                """)
                results['users_inserted'] = 'SUCCESS' if result is not None else 'NO_CHANGE'
            except Exception as e:
                results['users_inserted'] = f'ERROR: {str(e)}'
            
            # テスト商品作成（1つずつ）
            products = [
                ('ノートパソコン', '高性能ノートパソコンです', 120000.00, 10, '電子機器', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop'),
                ('スマートフォン', '最新スマートフォンです', 80000.00, 15, '電子機器', 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop'),
                ('ヘッドフォン', '高音質ヘッドフォンです', 15000.00, 20, '電子機器', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop'),
                ('デスク', '快適なデスクです', 20000.00, 5, '家具', 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop'),
                ('椅子', '人間工学に基づいた椅子です', 30000.00, 8, '家具', 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=400&h=300&fit=crop')
            ]
            
            inserted_count = 0
            for i, (name, desc, price, stock, category, image_url) in enumerate(products):
                try:
                    result = db_config.execute_update(
                        "INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                        (name, desc, price, stock, category, image_url)
                    )
                    if result is not None:
                        inserted_count += 1
                except Exception as e:
                    results[f'product_{i+1}_error'] = str(e)
            
            results['products_inserted'] = f'{inserted_count}/{len(products)} products'
            
            return jsonify({
                'success': inserted_count > 0,
                'message': f'初期データ投入: ユーザー{results.get("users_inserted", "UNKNOWN")}, 商品{inserted_count}件',
                'details': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'データ投入エラー'
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
    
    # 最優先: メインページルート（ブループリント登録前に定義）
    @app.route('/')
    def main_index():
        """メインページ - ショッピングモールのトップページ"""
        try:
            from app.database import db_config
            from flask import render_template
            
            print("🔄 メインページ表示処理開始...")
            
            # 人気商品を取得
            featured_products = db_config.execute_query(
                "SELECT * FROM products ORDER BY id DESC LIMIT 4"
            ) or []
            
            print(f"📦 取得商品数: {len(featured_products)}")
            
            # 最新レビューを取得
            recent_reviews = db_config.execute_query("""
                SELECT r.*, u.username, p.name as product_name, p.image_url 
                FROM reviews r 
                JOIN users u ON r.user_id = u.id 
                JOIN products p ON r.product_id = p.id 
                ORDER BY r.created_at DESC LIMIT 10
            """) or []
            
            print(f"💬 取得レビュー数: {len(recent_reviews)}")
            
            # HTMLテンプレートでレンダリング
            print("🎨 HTMLテンプレート使用")
            return render_template('main/index.html', 
                                 featured_products=featured_products, 
                                 recent_reviews=recent_reviews,
                                 review_query='')
                                 
        except Exception as e:
            print(f"❌ メインページエラー: {e}")
            import traceback
            traceback.print_exc()
            
            # 最後のフォールバック: 基本HTML直接出力
            featured_products = []
            try:
                from app.database import db_config
                featured_products = db_config.execute_query(
                    "SELECT * FROM products ORDER BY id DESC LIMIT 4"
                ) or []
            except:
                pass
            
            return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 脆弱なショッピングモール</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="text-center py-5">
            <h1 class="display-5 fw-bold mb-3">🔒 脆弱なショッピングモール</h1>
            <p class="lead text-muted mb-4">ウェブセキュリティ演習用のショッピングサイトです</p>
            <p class="text-warning">⚠️ このサイトは学習目的のみで使用してください</p>
        </div>
        
        <div class="row mt-5">
            <div class="col-md-12">
                <h4 class="mb-4">人気商品 ({len(featured_products)}件)</h4>
                <div class="row">
                    {"".join([f'''
                    <div class="col-md-3 mb-4">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-title">{p[1] if len(p) > 1 else "商品名"}</h6>
                                <p class="card-text">¥{p[3]:,.0f}</p>
                                <p class="card-text text-muted">{p[2] if len(p) > 2 else ""}</p>
                            </div>
                        </div>
                    </div>
                    ''' for p in featured_products[:4]])}
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-12">
                <h5>📍 機能へのアクセス</h5>
                <ul class="list-group">
                    <li class="list-group-item"><a href="/products">🛍️ 商品一覧</a></li>
                    <li class="list-group-item"><a href="/auth/register">👤 新規登録</a></li>
                    <li class="list-group-item"><a href="/auth/login">🔑 ログイン</a></li>
                    <li class="list-group-item"><a href="/health">🔧 ヘルスチェック</a></li>
                </ul>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # ブループリント登録
    try:
        from app.routes import main, auth, product, cart, order, review, admin, user, api, mail
        
        # メインブループリント以外を登録（メインページは上で直接定義済み）
        app.register_blueprint(auth.bp)
        app.register_blueprint(product.bp)
        app.register_blueprint(cart.bp)
        app.register_blueprint(order.bp)
        app.register_blueprint(review.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(user.bp)
        app.register_blueprint(api.bp)
        app.register_blueprint(mail.bp)
        
        print("✅ ブループリント登録完了（mainページ除く）")
        
    except ImportError as e:
        print(f"❌ ブループリント登録エラー: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️ 一部ブループリントの登録に失敗しましたが、メインページは動作します")
    
    # 環境変数とSupabase設定確認
    @app.route('/api/config-check')
    def config_check():
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            database_url = os.getenv('DATABASE_URL')
            
            config_info = {
                'supabase_url': supabase_url,
                'supabase_key_length': len(supabase_key) if supabase_key else 0,
                'database_url_preview': database_url[:80] + '...' if database_url and len(database_url) > 80 else database_url,
                'database_url_length': len(database_url) if database_url else 0
            }
            
            # DATABASE_URLの分析
            url_analysis = {}
            if database_url and 'postgresql://' in database_url:
                try:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(database_url)
                    
                    url_analysis = {
                        'hostname': parsed.hostname,
                        'port': parsed.port,
                        'database': parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
                        'username': parsed.username,
                        'is_supabase_direct': 'supabase.co' in (parsed.hostname or ''),
                        'is_aws_pooled': 'amazonaws.com' in (parsed.hostname or ''),
                        'connection_type': 'Direct' if 'supabase.co' in (parsed.hostname or '') else 'Pooled (AWS)' if 'amazonaws.com' in (parsed.hostname or '') else 'Unknown'
                    }
                    
                    # Direct URLの推奨
                    if url_analysis['is_aws_pooled'] and 'ucekealywqkiirpndaut' in database_url:
                        suggested_direct_url = database_url.replace(parsed.hostname, 'db.ucekealywqkiirpndaut.supabase.co')
                        url_analysis['suggested_direct_url'] = suggested_direct_url[:80] + '...' if len(suggested_direct_url) > 80 else suggested_direct_url
                        
                except Exception as parse_error:
                    url_analysis['parse_error'] = str(parse_error)
            
            return jsonify({
                'success': True,
                'config': config_info,
                'url_analysis': url_analysis,
                'recommendations': {
                    'use_direct_url': url_analysis.get('is_aws_pooled', False),
                    'current_connection_type': url_analysis.get('connection_type', 'Unknown')
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })

    # 強制SQLiteフォールバック有効化
    @app.route('/api/enable-fallback')
    def enable_fallback():
        try:
            import os
            import sqlite3
            
            # フォールバックモードを強制有効化
            os.environ['FALLBACK_MODE'] = 'true'
            
            # SQLiteデータベースを初期化
            from app.database import db_config
            db_config._initialize_sqlite_fallback()
            
            # テスト接続
            conn = db_config.get_db_connection()
            cursor = conn.cursor()
            
            # データ確認
            cursor.execute("SELECT COUNT(*) as user_count FROM users")
            user_count_result = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as product_count FROM products") 
            product_count_result = cursor.fetchone()
            
            cursor.execute("SELECT name, price FROM products LIMIT 3")
            sample_products = cursor.fetchall()
            
            conn.close()
            
            # SQLiteの結果を正しく処理
            user_count = 0
            product_count = 0
            
            if user_count_result:
                user_count = user_count_result['user_count'] if isinstance(user_count_result, dict) else user_count_result[0]
            
            if product_count_result:
                product_count = product_count_result['product_count'] if isinstance(product_count_result, dict) else product_count_result[0]
            
            return jsonify({
                'success': True,
                'method': 'sqlite_fallback',
                'message': 'SQLiteフォールバック有効化成功',
                'users_count': user_count,
                'products_count': product_count,
                'sample_products': [dict(row) for row in sample_products] if sample_products else [],
                'debug_info': {
                    'user_count_raw': dict(user_count_result) if user_count_result else None,
                    'product_count_raw': dict(product_count_result) if product_count_result else None,
                    'fallback_mode': os.getenv('FALLBACK_MODE')
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })

    # SQLiteフォールバック接続テスト
    @app.route('/api/fallback-test')
    def fallback_test():
        try:
            # SQLiteフォールバックでアプリケーションを動作させる
            import sqlite3
            import os
            
            # 一時的なSQLiteデータベースを作成
            db_path = '/tmp/fallback.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 基本テーブルを作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    description TEXT,
                    image_url TEXT,
                    category TEXT
                )
            ''')
            
            # テストデータ挿入
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password, email, role) 
                VALUES ('admin', 'admin123', 'admin@shop.com', 'admin')
            """)
            
            cursor.execute("""
                INSERT OR IGNORE INTO products (name, price, description, category) 
                VALUES ('Test Product', 19.99, 'テスト商品です', 'electronics')
            """)
            
            conn.commit()
            
            # データ確認
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'method': 'sqlite_fallback',
                'message': 'SQLite fallback database created successfully',
                'users_count': len(users),
                'products_count': len(products),
                'sample_users': users[:2],
                'sample_products': products[:2]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })

    # 代替接続エンドポイント（IPv6無効・IPv4強制）
    @app.route('/api/alt-connect')
    def alt_connect():
        try:
            # 代替のDATABASE_URL形式を試行
            original_url = os.getenv('DATABASE_URL')
            if not original_url:
                return jsonify({'error': 'DATABASE_URL not set'})
            
            # Supabaseの代替接続方法
            alternate_urls = []
            
            # 1. IPv4を強制する設定
            if 'aws-0-ap-northeast-1.compute.amazonaws.com' in original_url:
                # pooler-mode (port 6543) を試行
                pooler_url = original_url.replace(':5432/', ':6543/')
                alternate_urls.append(('pooler_mode', pooler_url))
                
                # direct-mode を試行
                direct_url = original_url.replace('aws-0-ap-northeast-1.compute.amazonaws.com', 'db.ucekealywqkiirpndaut.supabase.co')
                alternate_urls.append(('direct_mode', direct_url))
                
                # IPv4アドレス直接接続を試行（DNS回避）
                # Supabaseの一般的なIPアドレス範囲
                ipv4_addresses = [
                    '54.230.149.200',  # AWS CloudFront IP例
                    '52.84.106.25',    # AWS CloudFront IP例  
                    '3.33.155.128'     # AWS CloudFront IP例
                ]
                
                for ip in ipv4_addresses:
                    ip_url = original_url.replace('aws-0-ap-northeast-1.compute.amazonaws.com', ip)
                    alternate_urls.append((f'ipv4_direct_{ip}', ip_url))
                
                # SSL無効での接続も試行
                ssl_disabled_url = original_url + '?sslmode=disable'
                alternate_urls.append(('ssl_disabled', ssl_disabled_url))
            
            results = []
            
            for method, url in alternate_urls:
                try:
                    import psycopg2
                    from psycopg2.extras import RealDictCursor
                    
                    conn = psycopg2.connect(
                        url,
                        cursor_factory=RealDictCursor,
                        connect_timeout=10
                    )
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 as success, current_database() as db")
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    return jsonify({
                        'success': True,
                        'method': method,
                        'result': dict(result) if result else None,
                        'url_used': url[:60] + '...' if len(url) > 60 else url
                    })
                    
                except Exception as e:
                    results.append({
                        'method': method,
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
            
            return jsonify({
                'success': False,
                'message': 'All alternate methods failed',
                'attempts': results,
                'original_url_preview': original_url[:60] + '...' if len(original_url) > 60 else original_url
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })
    
    # 高度な接続診断テスト
    @app.route('/api/simple-test')
    def simple_test():
        try:
            # 環境変数の確認
            database_url = os.getenv('DATABASE_URL')
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not database_url:
                return jsonify({
                    'success': False,
                    'error': 'DATABASE_URL not set',
                    'error_type': 'ConfigurationError'
                })
            
            # 複数の接続方法を試行
            connection_attempts = []
            
            # 方法1: 元のDATABASE_URLで接続（タイムアウト設定あり）
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                
                conn = psycopg2.connect(
                    database_url, 
                    cursor_factory=RealDictCursor,
                    connect_timeout=15,
                    application_name='vulnerable_shop_test'
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test_value, current_database(), current_user")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'method': 'direct_psycopg2',
                    'message': 'Database connection successful',
                    'test_result': dict(result) if result else None,
                    'database_url_preview': database_url[:50] + '...' if len(database_url) > 50 else database_url
                })
                
            except Exception as e1:
                connection_attempts.append({
                    'method': 'direct_psycopg2',
                    'error': str(e1),
                    'error_type': type(e1).__name__
                })
            
            # 方法2: Supabaseクライアント経由
            if supabase_url and supabase_key:
                try:
                    from supabase import create_client
                    supabase_client = create_client(supabase_url, supabase_key)
                    
                    # REST APIでテーブル一覧取得を試行
                    response = supabase_client.rpc('version', {}).execute()
                    
                    return jsonify({
                        'success': True,
                        'method': 'supabase_client',
                        'message': 'Supabase client connection successful',
                        'test_result': response.data if hasattr(response, 'data') else str(response),
                        'supabase_url': supabase_url
                    })
                    
                except Exception as e2:
                    connection_attempts.append({
                        'method': 'supabase_client',
                        'error': str(e2),
                        'error_type': type(e2).__name__
                    })
            
            # 方法3: 手動解析したパラメータで接続
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(database_url)
                
                # ホスト名のIPアドレス解決を試行
                import socket
                try:
                    ip_address = socket.gethostbyname(parsed.hostname)
                    connection_attempts.append({
                        'dns_resolution': f'SUCCESS: {parsed.hostname} -> {ip_address}'
                    })
                except Exception as dns_e:
                    connection_attempts.append({
                        'dns_resolution': f'FAILED: {str(dns_e)}'
                    })
                
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    database=parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
                    user=parsed.username,
                    password=parsed.password,
                    cursor_factory=RealDictCursor,
                    connect_timeout=15
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test_value, version()")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'method': 'manual_parsing',
                    'message': 'Database connection successful via manual parsing',
                    'test_result': dict(result) if result else None,
                    'connection_info': {
                        'host': parsed.hostname,
                        'port': parsed.port or 5432,
                        'database': parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
                        'user': parsed.username
                    }
                })
                
            except Exception as e3:
                connection_attempts.append({
                    'method': 'manual_parsing',
                    'error': str(e3),
                    'error_type': type(e3).__name__
                })
            
            # すべての方法が失敗した場合
            return jsonify({
                'success': False,
                'error': 'All connection methods failed',
                'error_type': 'ConnectionError',
                'attempts': connection_attempts,
                'environment_info': {
                    'has_database_url': bool(database_url),
                    'has_supabase_url': bool(supabase_url),
                    'has_supabase_key': bool(supabase_key),
                    'database_url_length': len(database_url) if database_url else 0
                }
            }), 500
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }), 500
    
    # 直接SQL実行エンドポイント（診断用）
    @app.route('/api/raw-sql')
    def raw_sql():
        try:
            from app.database import db_config
            
            # 複数のクエリで詳細な情報を取得
            queries = {
                'pg_tables': "SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('information_schema', 'pg_catalog')",
                'pg_namespace': "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'",
                'current_schemas': "SELECT unnest(current_schemas(true)) as schema_name",
                'table_count': "SELECT count(*) as total_tables FROM information_schema.tables WHERE table_type = 'BASE TABLE'"
            }
            
            results = {}
            for name, sql in queries.items():
                try:
                    results[name] = db_config.execute_query(sql)
                except Exception as e:
                    results[name] = f"Error: {str(e)}"
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app 