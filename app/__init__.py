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
    
    # シンプルテーブル作成テスト
    @app.route('/api/simple-test')
    def simple_test():
        try:
            import psycopg2
            import psycopg2.extras
            
            # 直接psycopg2で接続してテスト
            conn = psycopg2.connect(
                os.getenv('DATABASE_URL'),
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # シンプルなテーブル作成テスト
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """)
            
            # テストデータ挿入
            cursor.execute("INSERT INTO test_table (name) VALUES ('test') RETURNING id")
            insert_result = cursor.fetchone()
            
            # データ確認
            cursor.execute("SELECT * FROM test_table LIMIT 5")
            result = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Direct connection test successful',
                'inserted_id': dict(insert_result) if insert_result else None,
                'table_data': [dict(row) for row in result]
            })
            
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