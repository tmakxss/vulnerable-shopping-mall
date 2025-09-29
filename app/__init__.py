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
    
    # 最優先: メインページルート（確実にHTMLを返す）
    @app.route('/')
    def main_index():
        """メインページ - ショッピングモールのトップページ（HTML直接出力）"""
        try:
            from app.database import db_config
            
            # 人気商品を取得
            featured_products = db_config.execute_query(
                "SELECT * FROM products ORDER BY id DESC LIMIT 4"
            ) or []
            
            # 商品データがない場合、デモ用のサンプルデータを使用
            if not featured_products:
                print("🔄 メインページ: 商品データが見つからないため、サンプル表示")
                featured_products = [
                    (1, 'MacBook Air M3', 'Ultra-thin laptop with M3 chip', 199999.0, 5, 'electronics', 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400&h=300&fit=crop', '2025-09-29'),
                    (2, 'AirPods Pro', 'Premium wireless earbuds', 39999.0, 10, 'electronics', 'https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=400&h=300&fit=crop', '2025-09-29'),
                    (3, 'Nike Air Max', 'Comfortable running shoes', 15999.0, 15, 'fashion', 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=300&fit=crop', '2025-09-29'),
                    (4, 'Sony Camera', 'Professional digital camera', 89999.0, 3, 'electronics', 'https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=400&h=300&fit=crop', '2025-09-29')
                ]
            
            # 商品カードHTML生成
            product_cards = ""
            for p in featured_products[:4]:
                try:
                    name = p[1] if len(p) > 1 else "商品名"
                    price = f"{p[3]:,.0f}" if len(p) > 3 else "価格未設定"
                    description = p[2][:50] + "..." if len(p) > 2 and p[2] else ""
                    
                    product_cards += f'''
                    <div class="col-md-3 col-sm-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <h6 class="card-title">{name}</h6>
                                <p class="card-text"><strong>¥{price}</strong></p>
                                <p class="card-text text-muted small">{description}</p>
                                <a href="/products" class="btn btn-primary btn-sm">詳細を見る</a>
                            </div>
                        </div>
                    </div>
                    '''
                except Exception as card_error:
                    print(f"商品カード生成エラー: {card_error}")
                    continue
            
            # 完全なHTMLページを生成
            html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 脆弱なショッピングモール</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css">
    <style>
        .hero-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 0;
        }}
        .product-card {{
            transition: transform 0.2s;
            border: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .product-card:hover {{
            transform: translateY(-5px);
        }}
        .navbar {{
            background: #2c3e50 !important;
        }}
        .navbar-brand {{
            font-weight: bold;
            color: #ecf0f1 !important;
        }}
    </style>
</head>
<body>
    <!-- ナビゲーションバー -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="bi bi-shield-exclamation"></i>
                脆弱なショッピングモール
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/products"><i class="bi bi-bag"></i> 商品</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/auth/login"><i class="bi bi-person"></i> ログイン</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/auth/register"><i class="bi bi-person-plus"></i> 新規登録</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- ヒーローセクション -->
    <div class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 fw-bold mb-3">
                <i class="bi bi-shield-exclamation"></i>
                脆弱なショッピングモール
            </h1>
            <p class="lead mb-4">ウェブセキュリティ演習用のショッピングサイトです</p>
            <div class="alert alert-warning d-inline-block" role="alert">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>注意:</strong> このサイトは学習目的のみで使用してください
            </div>
            <div class="mt-4">
                <a href="/products" class="btn btn-light btn-lg me-3">
                    <i class="bi bi-bag"></i> 商品を見る
                </a>
                <a href="/health" class="btn btn-outline-light btn-lg">
                    <i class="bi bi-gear"></i> システム状態
                </a>
            </div>
        </div>
    </div>

    <!-- メインコンテンツ -->
    <div class="container my-5">
        <!-- 人気商品セクション -->
        <section class="mb-5">
            <h2 class="text-center mb-4">
                <i class="bi bi-star-fill text-warning"></i>
                人気商品 ({len(featured_products)}件)
            </h2>
            <div class="row">
                {product_cards}
            </div>
            {('<div class="text-center mt-4"><p class="text-muted">商品データを読み込み中...</p></div>' if not featured_products else '')}
        </section>

        <!-- 機能紹介セクション -->
        <section class="mb-5">
            <h3 class="text-center mb-4">
                <i class="bi bi-list-check"></i>
                利用可能な機能
            </h3>
            <div class="row">
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <i class="bi bi-bag-check display-6 text-primary"></i>
                            <h5 class="card-title mt-3">商品閲覧</h5>
                            <p class="card-text">様々な商品を閲覧できます</p>
                            <a href="/products" class="btn btn-primary">商品一覧</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <i class="bi bi-person-plus display-6 text-success"></i>
                            <h5 class="card-title mt-3">新規登録</h5>
                            <p class="card-text">アカウントを作成できます</p>
                            <a href="/auth/register" class="btn btn-success">登録</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <i class="bi bi-key display-6 text-info"></i>
                            <h5 class="card-title mt-3">ログイン</h5>
                            <p class="card-text">既存アカウントでログイン</p>
                            <a href="/auth/login" class="btn btn-info">ログイン</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <i class="bi bi-gear display-6 text-secondary"></i>
                            <h5 class="card-title mt-3">システム状態</h5>
                            <p class="card-text">システム情報を確認</p>
                            <a href="/health" class="btn btn-secondary">確認</a>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- フッター -->
    <footer class="bg-dark text-light py-4 mt-5">
        <div class="container text-center">
            <p class="mb-0">
                <i class="bi bi-shield-exclamation"></i>
                脆弱なショッピングモール - ウェブセキュリティ学習サイト
            </p>
            <p class="text-muted small mt-2">学習目的のみでご使用ください</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
            
            return html_content
            
        except Exception as e:
            # エラーが発生した場合の最小限のHTMLページ
            return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>🔒 脆弱なショッピングモール</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5 text-center">
        <h1>🔒 脆弱なショッピングモール</h1>
        <p class="lead">ウェブセキュリティ演習サイト</p>
        <div class="alert alert-warning">⚠️ このサイトは学習目的のみで使用してください</div>
        <p>エラーが発生しました: {str(e)}</p>
        <a href="/health" class="btn btn-primary">システム状態を確認</a>
    </div>
</body>
</html>'''

    # 追加ルート: 商品一覧ページ（mainブループリントから移植）
    @app.route('/products')
    def products_list():
        """商品一覧ページ"""
        try:
            from app.database import db_config
            from flask import request
            
            # カテゴリ、検索、ソート機能
            category = request.args.get('category', '')
            search = request.args.get('search', '')
            sort = request.args.get('sort', 'id')
            
            # SQLクエリ構築
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if search:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            # ソート順序
            if sort == 'price_asc':
                query += " ORDER BY price ASC"
            elif sort == 'price_desc':
                query += " ORDER BY price DESC"
            elif sort == 'name':
                query += " ORDER BY name ASC"
            else:
                query += " ORDER BY id DESC"
            
            products = db_config.execute_query(query, params) or []
            
            # 商品データがない場合、サンプルデータを作成
            if not products:
                print("🔄 商品データが見つからないため、サンプルデータを作成中...")
                sample_products = [
                    ('MacBook Air M3', 'Ultra-thin laptop with M3 chip', 199999.0, 5, 'electronics', '/static/uploads/macbook.jpg'),
                    ('AirPods Pro', 'Premium wireless earbuds', 39999.0, 10, 'electronics', '/static/uploads/airpods.jpg'),
                    ('Nike Air Max', 'Comfortable running shoes', 15999.0, 15, 'fashion', '/static/uploads/nike.jpg'),
                    ('Sony Camera', 'Professional digital camera', 89999.0, 3, 'electronics', '/static/uploads/camera.jpg'),
                    ('デスクチェア', '人間工学に基づいたオフィスチェア', 45999.0, 8, 'furniture', '/static/uploads/chair.jpg'),
                    ('スマートウォッチ', 'フィットネス追跡機能付き', 29999.0, 12, 'electronics', '/static/uploads/watch.jpg')
                ]
                
                try:
                    # テーブル作成を試行
                    db_config.execute_update("""
                        CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            description TEXT,
                            price REAL NOT NULL,
                            stock INTEGER DEFAULT 0,
                            category TEXT,
                            image_url TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # サンプルデータ挿入
                    for product_data in sample_products:
                        db_config.execute_update(
                            "INSERT OR IGNORE INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                            product_data
                        )
                    
                    # 再度商品データを取得
                    products = db_config.execute_query(query, params) or []
                    print(f"✅ サンプルデータ作成完了: {len(products)}件の商品")
                    
                except Exception as sample_error:
                    print(f"❌ サンプルデータ作成エラー: {sample_error}")
                    # ハードコードされたフォールバックデータ
                    products = [
                        (1, 'MacBook Air M3', 'Ultra-thin laptop with M3 chip', 199999.0, 5, 'electronics', '/static/uploads/macbook.jpg', '2025-09-29'),
                        (2, 'AirPods Pro', 'Premium wireless earbuds', 39999.0, 10, 'electronics', '/static/uploads/airpods.jpg', '2025-09-29'),
                        (3, 'Nike Air Max', 'Comfortable running shoes', 15999.0, 15, 'fashion', '/static/uploads/nike.jpg', '2025-09-29'),
                        (4, 'Sony Camera', 'Professional digital camera', 89999.0, 3, 'electronics', '/static/uploads/camera.jpg', '2025-09-29')
                    ]
            
            # カテゴリ一覧取得
            categories = db_config.execute_query(
                "SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category"
            ) or []
            
            # カテゴリデータがない場合のフォールバック
            if not categories and products:
                categories = [('electronics',), ('fashion',), ('furniture',)]
            
            # 商品カード生成
            product_cards = ""
            for product in products:
                try:
                    name = product[1] if len(product) > 1 else "商品名"
                    price = f"{product[3]:,.0f}" if len(product) > 3 else "価格未設定"
                    description = product[2][:100] + "..." if len(product) > 2 and product[2] else ""
                    image_url = product[6] if len(product) > 6 and product[6] else "/static/uploads/no-image.jpg"
                    product_id = product[0] if len(product) > 0 else ""
                    
                    product_cards += f'''
                    <div class="col-md-4 col-sm-6 mb-4">
                        <div class="card product-card h-100">
                            <img src="{image_url}" class="card-img-top" alt="{name}" style="height: 200px; object-fit: cover;">
                            <div class="card-body d-flex flex-column">
                                <h6 class="card-title">{name}</h6>
                                <p class="card-text text-muted small">{description}</p>
                                <div class="mt-auto">
                                    <p class="product-price mb-3"><strong>¥{price}</strong></p>
                                    <a href="/product/{product_id}" class="btn btn-primary btn-sm">詳細を見る</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    '''
                except Exception as card_error:
                    print(f"商品カード生成エラー: {card_error}")
                    continue
            
            # カテゴリオプション生成
            category_options = ""
            for cat in categories:
                cat_name = cat[0] if isinstance(cat, (list, tuple)) else cat
                selected = "selected" if cat_name == category else ""
                category_options += f'<option value="{cat_name}" {selected}>{cat_name}</option>'
            
            # HTMLページ生成
            html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商品一覧 - 脆弱なショッピングモール</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css">
    <style>
        .product-card {{ transition: transform 0.2s; border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .product-card:hover {{ transform: translateY(-5px); }}
        .navbar {{ background: #2c3e50 !important; }}
    </style>
</head>
<body>
    <!-- ナビゲーションバー -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="bi bi-shield-exclamation"></i> 脆弱なショッピングモール</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="bi bi-house"></i> ホーム</a>
                <a class="nav-link active" href="/products"><i class="bi bi-bag"></i> 商品</a>
                <a class="nav-link" href="/auth/login"><i class="bi bi-person"></i> ログイン</a>
            </div>
        </div>
    </nav>

    <div class="container my-5">
        <h1 class="mb-4"><i class="bi bi-bag-check"></i> 商品一覧 ({len(products)}件)</h1>
        
        <!-- 検索・フィルター -->
        <div class="row mb-4">
            <div class="col-md-12">
                <form method="GET" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">検索</label>
                        <input type="text" class="form-control" name="search" value="{search}" placeholder="商品名・説明で検索">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">カテゴリ</label>
                        <select class="form-select" name="category">
                            <option value="">全てのカテゴリ</option>
                            {category_options}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">並び順</label>
                        <select class="form-select" name="sort">
                            <option value="id" {"selected" if sort == "id" else ""}>新着順</option>
                            <option value="name" {"selected" if sort == "name" else ""}>名前順</option>
                            <option value="price_asc" {"selected" if sort == "price_asc" else ""}>価格安い順</option>
                            <option value="price_desc" {"selected" if sort == "price_desc" else ""}>価格高い順</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">&nbsp;</label>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary"><i class="bi bi-search"></i> 検索</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- 商品一覧 -->
        <div class="row">
            {product_cards}
        </div>
        
        {('<div class="text-center mt-5"><div class="alert alert-info"><h5>商品データがありません</h5><p>データベースを初期化してサンプル商品を追加してください。</p><a href="/api/create-tables" class="btn btn-warning me-2">テーブル作成</a><a href="/api/seed-data" class="btn btn-success">サンプルデータ追加</a><a href="/products" class="btn btn-primary ms-2">再読み込み</a></div></div>' if not products else '')}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
            
            return html_content
            
        except Exception as e:
            return f'''<!DOCTYPE html>
<html><head><title>エラー</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body><div class="container mt-5"><h1>商品一覧エラー</h1><p>エラー: {str(e)}</p><a href="/" class="btn btn-primary">ホームに戻る</a></div></body></html>'''

    # ブループリント登録
    try:
        from app.routes import main, auth, product, cart, order, review, admin, user, api, mail
        
        # 全ブループリント登録（メインページは重複しないよう注意）
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