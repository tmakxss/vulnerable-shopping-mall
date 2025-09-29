#!/usr/bin/env python3
"""
Supabase接続情報確認スクリプト
"""

import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

print("=== Supabase接続情報確認 ===\n")

# 現在の環境変数を表示
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY') 
database_url = os.getenv('DATABASE_URL')

print(f"SUPABASE_URL: {supabase_url}")
print(f"SUPABASE_KEY: {'あり' if supabase_key else 'なし'} ({len(supabase_key)}文字)" if supabase_key else "SUPABASE_KEY: なし")
print(f"DATABASE_URL: {database_url}")

if database_url:
    print(f"\n=== DATABASE_URL分析 ===")
    print(f"長さ: {len(database_url)}文字")
    
    # URLの構成要素を分析
    if 'postgresql://' in database_url:
        parts = database_url.replace('postgresql://', '').split('@')
        if len(parts) == 2:
            user_pass = parts[0]
            host_db = parts[1]
            
            print(f"ユーザー部分: {user_pass.split(':')[0]}")
            print(f"ホスト部分: {host_db.split('/')[0]}")
            print(f"データベース名: {host_db.split('/')[-1]}")
            
            # ホスト名を確認
            hostname = host_db.split('/')[0].split(':')[0]
            print(f"\n現在のホスト名: {hostname}")
            
            # 正しいSupabaseのホスト名かチェック
            if 'supabase.co' in hostname:
                print("✅ 正しいSupabaseのDirect URLです")
            elif 'amazonaws.com' in hostname:
                print("❌ AWSのPooled接続URLです - Direct URLに変更が必要")
                # プロジェクトIDを推測
                if 'ucekealywqkiirpndaut' in database_url:
                    suggested_url = database_url.replace(hostname, 'db.ucekealywqkiirpndaut.supabase.co').replace(':5432', ':5432')
                    print(f"\n💡 推奨Direct URL:")
                    print(f"   {suggested_url}")
            else:
                print("⚠️  不明なホスト名です")

print(f"\n=== 次のステップ ===")
if 'amazonaws.com' in (database_url or ''):
    print("1. SupabaseダッシュボードでDirect URLを確認")
    print("2. VercelでDATABASE_URL環境変数を更新")
    print("3. 再デプロイしてテスト")
else:
    print("DATABASE_URLは正しく設定されているようです")