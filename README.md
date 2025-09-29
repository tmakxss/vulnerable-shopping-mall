# 🔒 脆弱なショッピングモール - ウェブセキュリティ演習サイト

ウェブセキュリティの学習と演習のための脆弱性を含むショッピングサイトです。

## 🌐 公開サイト

このサイトはVercelにデプロイされ、SupabaseをデータベースとしてPaaS環境で公開されています。

**公開URL**: [デプロイ後にURLが表示されます]

## 🚀 ローカル セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーし、必要な環境変数を設定：

```bash
cp .env.example .env
```

### 3. データベースの初期化

**ローカル開発の場合:**
```bash
python database/init_db.py
```

**Supabaseの場合:**
1. Supabaseプロジェクトを作成
2. `database/supabase_init.sql` をSQL Editorで実行
3. 環境変数にSupabase接続情報を設定

### 4. サーバーの起動

```bash
python run.py
```

### 5. アクセス

ブラウザで `http://localhost:5000` にアクセス

## ☁️ デプロイメント

### Vercel + Supabaseでのデプロイ手順

1. **GitHub リポジトリの作成**
2. **Supabase セットアップ**
   - Supabaseでプロジェクト作成
   - `database/supabase_init.sql` を実行
3. **Vercel デプロイ**
   - GitHubリポジトリをVercelに接続
   - 環境変数を設定

## 👥 テスト用アカウント

| ユーザー名 | パスワード  | 権限         |
| ---------- | ----------- | ------------ |
| admin      | admin123    | 管理者       |
| user1      | password123 | 一般ユーザー |
| test       | test123     | 一般ユーザー |

## 🔧 技術仕様

- **フレームワーク**: Flask (Python)
- **データベース**: 
  - 本番環境: Supabase (PostgreSQL)
  - ローカル開発: SQLite
- **デプロイ**: Vercel
- **フロントエンド**: Bootstrap 5
- **言語**: 日本語
- **追加機能**: データベースバックアップ, メールシステム, JSP Web Shell

## 🚨 含まれる脆弱性

### 1. SQL Injection

- ログイン機能
- 検索機能
- ユーザープロフィール

### 2. Cross-Site Scripting (XSS)

- レビュー投稿
- 検索結果表示
- ユーザー登録

### 3. **権限昇格脆弱性 (Privilege Escalation)**

- **隠しパラメータによる権限変更**
- ログイン時に `role` パラメータにより権限昇格可能
- サポートされる役割: `user`, `admin`, `super_admin`, `moderator`

### 4. **ファイルアップロード脆弱性**

- **Directory Traversal**
- メール添付ファイルでのパストラバーサル攻撃
- 不適切なファイル名検証

### 5. **データベース操作脆弱性**

- **Path Traversal in Backup**
- バックアップファイル名でのディレクトリトラバーサル
- 不適切なファイル名検証

### 6. その他の脆弱性

- 不適切な認証・認可
- 情報漏洩
- コマンドインジェクション
- JSP Web Shell (学習用)

## 📁 プロジェクト構造

```
exploit_server/
├── app/
│   ├── routes/          # ルーティング
│   ├── templates/       # HTMLテンプレート
│   ├── static/          # CSS/JS/画像
│   └── web.jsp          # JSP Web Shell (学習用)
├── database/            # データベース
├── requirements.txt     # 依存関係
└── run.py              # 起動スクリプト
```

## ⚠️ 注意事項

- **このサイトは学習目的のみで使用してください**
- **実際の Web サイトでの攻撃は違法です**
- **本番環境では絶対に使用しないでください**
- **適切なセキュリティ対策を実装してください**

## 📞 サポート

このプロジェクトに関する質問や問題がある場合は、イシューを作成してください。

---

**🔒 セキュリティ学習を楽しんでください！**
