# Vercelでの環境変数設定手順

## 🔧 Vercelダッシュボードで以下の環境変数を設定してください

1. Vercelダッシュボードにアクセス: https://vercel.com/dashboard
2. プロジェクト「vulnerable-shopping-mall」を選択
3. Settings → Environment Variables

## 📝 設定する環境変数

### SUPABASE_URL
```
https://[your-project-id].supabase.co
```

### SUPABASE_KEY
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (anon public key)
```

### DATABASE_URL
```
postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres
```

### FLASK_SECRET_KEY
```
vulnerable_shop_secret_key_12345
```

### FLASK_ENV
```
production
```

## 🔍 Supabaseの情報取得方法

1. **SUPABASE_URL**: 
   - Supabaseダッシュボード → Settings → API
   - "Project URL" をコピー

2. **SUPABASE_KEY**:
   - Supabaseダッシュボード → Settings → API
   - "anon public" キーをコピー

3. **DATABASE_URL**:
   - Supabaseダッシュボード → Settings → Database
   - "Connection string" → "Pooler" → "Transaction" をコピー
   - [password] を実際のパスワードに置換

## ⚠️ 重要
環境変数設定後、Vercelで再デプロイが必要です。