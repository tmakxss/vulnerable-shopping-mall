import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        
        # 環境変数の確認
        print(f"🔍 SUPABASE_URL: {'✅' if self.supabase_url else '❌'}")
        print(f"🔍 DATABASE_URL: {'✅' if self.database_url else '❌'}")
        
        # 接続テストを実行してフォールバックを決定
        self.use_postgres = self._test_postgres_connection()
        
        # Supabaseクライアントの初期化
        if self.supabase_url and self.supabase_key and self.use_postgres:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabaseクライアント初期化成功")
            except Exception as e:
                print(f"❌ Supabaseクライアント初期化エラー: {e}")
                self.use_postgres = False
                
    def _test_postgres_connection(self):
        """PostgreSQLの接続テストを実行"""
        if not self.database_url:
            print("❌ DATABASE_URLが設定されていません - SQLiteにフォールバック")
            return False
            
        try:
            # 短いタイムアウトで接続テスト
            conn = psycopg2.connect(self.database_url, connect_timeout=3)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            print("✅ PostgreSQL接続成功")
            return True
        except Exception as e:
            print(f"❌ PostgreSQL接続失敗: {e}")
            print("🔄 SQLiteフォールバックモードを使用")
            
            # SQLiteデータベースの初期化
            self._initialize_sqlite_fallback()
            return False
    
    def _initialize_sqlite_fallback(self):
        """SQLiteフォールバックデータベースを初期化"""
        try:
            import sqlite3
            import os
            
            # Vercelの一時ディレクトリを使用
            db_path = '/tmp/fallback_shop.db'
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 基本テーブルを作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    description TEXT,
                    image_url TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 管理者ユーザーを作成
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password, email, role) 
                VALUES ('admin', 'admin123', 'admin@shop.com', 'admin')
            """)
            
            # サンプル商品を追加
            sample_products = [
                ('iPhone 15 Pro', 149999.0, 'Latest iPhone with advanced features', '/static/uploads/iphone.jpg', 'electronics'),
                ('MacBook Air M3', 199999.0, 'Ultra-thin laptop with M3 chip', '/static/uploads/macbook.jpg', 'electronics'),
                ('AirPods Pro', 39999.0, 'Premium wireless earbuds', '/static/uploads/airpods.jpg', 'electronics'),
                ('Nike Air Max', 15999.0, 'Comfortable running shoes', '/static/uploads/nike.jpg', 'fashion'),
                ('Sony Camera', 89999.0, 'Professional digital camera', '/static/uploads/camera.jpg', 'electronics')
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO products (name, price, description, image_url, category) 
                VALUES (?, ?, ?, ?, ?)
            """, sample_products)
            
            conn.commit()
            conn.close()
            
            print("✅ SQLiteフォールバックデータベース初期化完了")
            
            # DATABASE_URLをSQLiteパスに一時的に変更
            os.environ['FALLBACK_MODE'] = 'true'
            
        except Exception as e:
            print(f"❌ SQLiteフォールバック初期化失敗: {e}")
    
    def _get_sqlite_connection(self):
        """SQLite接続を取得"""
        import sqlite3
        
        db_path = '/tmp/fallback_shop.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return conn
        
    def get_db_connection(self):
        """データベース接続を取得（フォールバック対応）"""
        import os
        
        # フォールバックモードが有効な場合はSQLiteを使用
        if os.getenv('FALLBACK_MODE') == 'true':
            return self._get_sqlite_connection()
            
        try:
            if self.use_postgres and self.database_url:
                print(f"🔍 PostgreSQL接続試行: {self.database_url[:50]}...")
                
                # PostgreSQL/Supabase接続（接続パラメータを追加）
                conn = psycopg2.connect(
                    self.database_url,
                    cursor_factory=RealDictCursor,
                    connect_timeout=10,
                    application_name='vulnerable_shopping_mall'
                )
                
                # autocommitモードを設定（DDL文用）
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                
                # 接続テスト
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT current_database(), current_schema(), version()")
                    result = cursor.fetchone()
                    print(f"✅ PostgreSQL接続成功: DB={result[0]}, Schema={result[1]}")
                except Exception as e:
                    print(f"⚠️ 詳細情報取得失敗: {e}, でも接続は成功")
                
                return conn
            else:
                print("⚠️ DATABASE_URLが設定されていません、SQLiteを使用")
                
                # ローカル開発用のSQLite（本番環境でも環境変数がない場合のフォールバック）
                import os
                db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'shop.db')
                if not os.path.exists(db_path):
                    # SQLiteファイルが存在しない場合は作成
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row  # 辞書形式でアクセス
                print("✅ SQLite接続成功（フォールバック）")
                return conn
                
        except psycopg2.Error as e:
            print(f"❌ PostgreSQL接続エラー: {e}")
            print("⚠️ SQLiteにフォールバック")
            
            # PostgreSQL接続失敗時はSQLiteにフォールバック
            try:
                import os
                db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'shop.db')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                print("✅ SQLiteフォールバック接続成功")
                return conn
            except:
                # 最終フォールバック：メモリ内SQLite
                conn = sqlite3.connect(':memory:')
                conn.row_factory = sqlite3.Row
                print("⚠️ メモリ内SQLite使用（一時的）")
                return conn
                
        except Exception as e:
            print(f"❌ 一般的なデータベース接続エラー: {e}")
            return None
    
    def get_supabase_client(self):
        """Supabaseクライアントを取得"""
        return self.supabase if hasattr(self, 'supabase') else None
    
    def execute_query(self, query, params=None):
        """SQLクエリ実行（SELECT用）"""
        import os
        
        conn = self.get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            
            # フォールバックモードかPostgreSQL失敗の場合はSQLiteとして扱う
            is_sqlite_mode = (os.getenv('FALLBACK_MODE') == 'true' or not self.use_postgres)
            
            # PostgreSQLとSQLiteの構文違いを自動調整
            if not is_sqlite_mode and params:
                # PostgreSQLは%sプレースホルダー
                adjusted_query = query.replace('?', '%s')
                cursor.execute(adjusted_query, params)
            elif is_sqlite_mode and params:
                # SQLiteは?プレースホルダー
                adjusted_query = query.replace('%s', '?')
                cursor.execute(adjusted_query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            # PostgreSQLとSQLiteの結果を統一
            return [dict(row) for row in results]
                
        except Exception as e:
            print(f"❌ クエリ実行エラー: {e}")
            print(f"クエリ: {query}")
            print(f"パラメータ: {params}")
            return []
        finally:
            conn.close()
    
    def execute_update(self, query, params=None):
        """SQLクエリ実行（INSERT/UPDATE/DELETE用）"""
        import os
        
        conn = self.get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            
            # フォールバックモードかPostgreSQL失敗の場合はSQLiteとして扱う
            is_sqlite_mode = (os.getenv('FALLBACK_MODE') == 'true' or not self.use_postgres)
            
            # PostgreSQLとSQLiteの構文違いを自動調整
            if not is_sqlite_mode and params:
                # PostgreSQLは%sプレースホルダー
                adjusted_query = query.replace('?', '%s')
                cursor.execute(adjusted_query, params)
            elif is_sqlite_mode and params:
                # SQLiteは?プレースホルダー
                adjusted_query = query.replace('%s', '?')
                cursor.execute(adjusted_query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            
            # 挿入されたIDを返す
            if not is_sqlite_mode:  # PostgreSQL
                if query.strip().upper().startswith('INSERT'):
                    try:
                        cursor.execute('SELECT lastval()')
                        result = cursor.fetchone()
                        return result[0] if result else None
                    except:
                        return True  # 成功したが、IDが取得できない場合
            else:
                return cursor.lastrowid
                
        except Exception as e:
            conn.rollback()
            print(f"❌ 更新クエリエラー: {e}")
            print(f"クエリ: {query}")
            print(f"パラメータ: {params}")
            return None
        finally:
            conn.close()

# グローバルインスタンス
db_config = DatabaseConfig()