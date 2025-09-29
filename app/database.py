import os
import psycopg2
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        
        # Supabaseクライアントの初期化
        if self.supabase_url and self.supabase_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    def get_db_connection(self):
        """PostgreSQL接続を取得"""
        try:
            if self.database_url:
                return psycopg2.connect(self.database_url)
            else:
                # ローカル開発用のSQLite
                import sqlite3
                return sqlite3.connect('database/shop.db')
        except Exception as e:
            print(f"データベース接続エラー: {e}")
            return None
    
    def get_supabase_client(self):
        """Supabaseクライアントを取得"""
        return self.supabase if hasattr(self, 'supabase') else None

# グローバルインスタンス
db_config = DatabaseConfig()