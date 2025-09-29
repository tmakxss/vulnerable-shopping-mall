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
        self.use_postgres = bool(self.database_url)
        
        # Supabaseクライアントの初期化
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabaseクライアント初期化成功")
            except Exception as e:
                print(f"❌ Supabaseクライアント初期化エラー: {e}")
        
    def get_db_connection(self):
        """データベース接続を取得"""
        try:
            if self.use_postgres and self.database_url:
                # PostgreSQL/Supabase接続
                conn = psycopg2.connect(
                    self.database_url,
                    cursor_factory=RealDictCursor
                )
                print("✅ PostgreSQL接続成功")
                return conn
            else:
                # ローカル開発用のSQLite
                conn = sqlite3.connect('database/shop.db')
                conn.row_factory = sqlite3.Row  # 辞書形式でアクセス
                print("✅ SQLite接続成功")
                return conn
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
            return None
    
    def get_supabase_client(self):
        """Supabaseクライアントを取得"""
        return self.supabase if hasattr(self, 'supabase') else None
    
    def execute_query(self, query, params=None):
        """SQLクエリ実行（SELECT用）"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            # PostgreSQLとSQLiteの結果を統一
            return [dict(row) for row in results]
                
        except Exception as e:
            print(f"❌ クエリ実行エラー: {e}")
            return []
        finally:
            conn.close()
    
    def execute_update(self, query, params=None):
        """SQLクエリ実行（INSERT/UPDATE/DELETE用）"""
        conn = self.get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            
            # 挿入されたIDを返す
            if self.use_postgres:
                if query.strip().upper().startswith('INSERT'):
                    cursor.execute('SELECT lastval()')
                    result = cursor.fetchone()
                    return result[0] if result else None
            else:
                return cursor.lastrowid
                
        except Exception as e:
            conn.rollback()
            print(f"❌ 更新クエリエラー: {e}")
            return None
        finally:
            conn.close()

# グローバルインスタンス
db_config = DatabaseConfig()