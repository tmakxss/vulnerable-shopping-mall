# デプロイメント手順書

このプロジェクトをGitHub、Vercel、Supabaseを使用して公開するための詳細な手順書です。

## 前提条件

1. **Git のインストール**
   - [Git公式サイト](https://git-scm.com/downloads) からGitをダウンロード・インストール
   
2. **アカウントの準備**
   - [GitHub](https://github.com/) アカウント
   - [Vercel](https://vercel.com/) アカウント
   - [Supabase](https://supabase.com/) アカウント

## 手順 1: Supabase データベースのセットアップ

### 1.1 Supabaseプロジェクト作成
1. [Supabase](https://supabase.com/) にログイン
2. "New project" をクリック
3. プロジェクト名とパスワードを設定
4. リージョンを選択（Japan East推奨）
5. "Create new project" をクリック

### 1.2 データベース初期化
1. Supabaseダッシュボードで "SQL Editor" を開く
2. 本プロジェクトの `database/supabase_init.sql` の内容をコピー
3. SQL Editorに貼り付けて "Run" をクリック

### 1.3 接続情報の取得
1. "Settings" → "API" を開く
2. 以下の情報をメモ：
   - Project URL
   - anon public key
   - Database URL (Settings → Database)

## 手順 2: GitHub リポジトリの作成とコードのプッシュ

### 2.1 Git初期化（コマンドプロンプト/PowerShellで実行）
```bash
# プロジェクトディレクトリに移動
cd "c:\Users\tmakise\Documents\exploit_server1\exploit_server"

# Gitリポジトリ初期化
git init

# ファイルをステージングに追加
git add .

# 初回コミット
git commit -m "Initial commit: Vulnerable shopping mall for security training"

# GitHubのユーザー名とメールを設定（初回のみ）
git config --global user.name "Your GitHub Username"
git config --global user.email "your-email@example.com"
```

### 2.2 GitHub リポジトリ作成
1. [GitHub](https://github.com/) にログイン
2. "New repository" をクリック
3. Repository name: `vulnerable-shopping-mall`
4. Descriptionを入力
5. "Public" または "Private" を選択
6. "Create repository" をクリック

### 2.3 リモートリポジトリの設定とプッシュ
```bash
# GitHubリポジトリをリモートに追加（URLは作成したリポジトリのものに置き換え）
git remote add origin https://github.com/YOUR_USERNAME/vulnerable-shopping-mall.git

# メインブランチにプッシュ
git branch -M main
git push -u origin main
```

## 手順 3: Vercel でのデプロイ

### 3.1 Vercel プロジェクト作成
1. [Vercel](https://vercel.com/) にログイン
2. "New Project" をクリック
3. "Import Git Repository" で先ほど作成したGitHubリポジトリを選択
4. "Import" をクリック

### 3.2 環境変数の設定
1. Vercelプロジェクトの "Settings" → "Environment Variables" を開く
2. 以下の環境変数を追加：

```
SUPABASE_URL = your_supabase_project_url
SUPABASE_KEY = your_supabase_anon_key
DATABASE_URL = postgresql://postgres:[password]@[host]:5432/postgres
FLASK_SECRET_KEY = your_secure_secret_key_here
FLASK_ENV = production
```

### 3.3 デプロイ
1. "Deploy" をクリック
2. ビルドが完了するまで待機
3. デプロイ完了後、提供されるURLでサイトにアクセス

## 手順 4: 動作確認

### 4.1 基本機能テスト
1. デプロイされたサイトにアクセス
2. ユーザー登録・ログイン機能を確認
3. 商品表示機能を確認
4. 管理者機能を確認（admin / admin123）

### 4.2 データベース接続確認
1. 商品データが正しく表示されるか確認
2. ユーザー登録が正しく動作するか確認
3. ログインが正しく動作するか確認

## トラブルシューティング

### よくある問題と対処法

1. **ビルドエラーが発生する場合**
   - `requirements.txt` の依存関係を確認
   - Python バージョン互換性を確認

2. **データベース接続エラーが発生する場合**
   - 環境変数の設定を確認
   - Supabaseの接続情報を再確認

3. **静的ファイルが表示されない場合**
   - Vercelの静的ファイル配信設定を確認
   - CSSやJSのパスを確認

## セキュリティ注意事項

⚠️ **重要**: このプロジェクトは意図的に脆弱性を含むセキュリティ学習用サイトです。

- 実際の機密情報は絶対に使用しないでください
- 学習・教育目的以外での使用は避けてください
- 攻撃の実践は適切な環境でのみ行ってください

## サポート

デプロイメントで問題が発生した場合：
1. Vercelのデプロイログを確認
2. Supabaseのログを確認
3. 環境変数の設定を再確認
4. GitHubのIssuesで問題を報告

---

このドキュメントに従って、段階的にデプロイメントを進めてください。各手順での不明点があれば、適宜サポートいたします。