import os
import sqlite3
from typing import Optional, Any
try:
    import psycopg2
    import psycopg2.extras
    from supabase import create_client, Client
    from dotenv import load_dotenv
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# 環境変数を読み込み
if POSTGRES_AVAILABLE:
    load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL') if POSTGRES_AVAILABLE else None
        self.supabase_url = os.getenv('SUPABASE_URL') if POSTGRES_AVAILABLE else None
        self.supabase_key = os.getenv('SUPABASE_KEY') if POSTGRES_AVAILABLE else None
        
        # Supabaseクライアントの初期化
        if POSTGRES_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            except:
                self.supabase = None
        else:
            self.supabase = None
    
    def get_connection(self):
        """データベース接続を取得（PostgreSQL優先、フォールバックでSQLite）"""
        try:
            # 本番環境（PostgreSQL）
            if POSTGRES_AVAILABLE and self.database_url:
                conn = psycopg2.connect(self.database_url)
                conn.autocommit = True
                return conn
        except Exception as e:
            print(f"PostgreSQL接続エラー: {e}")
        
        # ローカル開発環境（SQLite）
        try:
            # データベースディレクトリが存在しない場合は作成
            os.makedirs('database', exist_ok=True)
            return sqlite3.connect('database/shop.db')
        except Exception as e:
            print(f"SQLite接続エラー: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None, fetchone: bool = False, fetchall: bool = False):
        """クエリを実行する汎用メソッド"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            if POSTGRES_AVAILABLE and self.database_url:
                # PostgreSQL用
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # SQLiteのプレースホルダー（?）をPostgreSQL用（%s）に変換
                    pg_query = query.replace('?', '%s')
                    cursor.execute(pg_query, params)
                    
                    if fetchone:
                        result = cursor.fetchone()
                        return dict(result) if result else None
                    elif fetchall:
                        results = cursor.fetchall()
                        return [dict(row) for row in results] if results else []
                    else:
                        conn.commit()
                        return True
            else:
                # SQLite用
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                if fetchone:
                    result = cursor.fetchone()
                    return dict(zip([col[0] for col in cursor.description], result)) if result else None
                elif fetchall:
                    results = cursor.fetchall()
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in results] if results else []
                else:
                    conn.commit()
                    return True
        except Exception as e:
            print(f"クエリ実行エラー: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    def get_supabase_client(self):
        """Supabaseクライアントを取得"""
        return self.supabase

# グローバルインスタンス
db_manager = DatabaseManager()

def get_db_connection():
    """下位互換性のための関数"""
    return db_manager.get_connection()