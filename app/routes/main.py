from flask import Blueprint, render_template, request, session, redirect, flash, jsonify
from app.database import db_config
import sqlite3

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """メインページ"""
    try:
        # 人気商品を取得
        featured_products = db_config.execute_query(
            "SELECT * FROM products ORDER BY id DESC LIMIT 4"
        )
        
        # レビュー検索機能
        review_query = request.args.get('review_search', '')
        
        if review_query:
            # レビュー検索 (SQLインジェクション対策済み、XSS脆弱性は残存)
            recent_reviews = db_config.execute_query("""
                SELECT r.*, u.username, p.name as product_name, p.image_url 
                FROM reviews r 
                JOIN users u ON r.user_id = u.id 
                JOIN products p ON r.product_id = p.id 
                WHERE r.comment LIKE ? OR u.username LIKE ? OR p.name LIKE ?
                ORDER BY r.created_at DESC LIMIT 10
            """, (f'%{review_query}%', f'%{review_query}%', f'%{review_query}%'))
        else:
            # 最新レビューを取得
            recent_reviews = db_config.execute_query("""
                SELECT r.*, u.username, p.name as product_name, p.image_url 
                FROM reviews r 
                JOIN users u ON r.user_id = u.id 
                JOIN products p ON r.product_id = p.id 
                ORDER BY r.created_at DESC LIMIT 10
            """)
        
        return render_template('main/index.html', 
                             featured_products=featured_products, 
                             recent_reviews=recent_reviews,
                             review_query=review_query)
                             
    except Exception as e:
        print(f"❌ メインページエラー: {e}")
        # エラー時はJSONレスポンス
        return jsonify({
            'message': '🔒 脆弱なショッピングモール - ウェブセキュリティ演習サイト',
            'status': 'running',
            'note': '⚠️ このサイトは学習目的のみで使用してください',
            'error': 'Template rendering failed - API mode active'
        })

@bp.route('/products')
def products():
    """商品一覧ページ"""
    try:
        category = request.args.get('category', '')
        page = request.args.get('page', 1, type=int)
        per_page = 9
        offset = (page - 1) * per_page
        
        if category:
            # カテゴリフィルター
            all_products = db_config.execute_query(
                "SELECT * FROM products WHERE category = ?",
                (category,)
            )
        else:
            all_products = db_config.execute_query("SELECT * FROM products")
        
        # ページング処理
        total_products = len(all_products)
        total_pages = (total_products + per_page - 1) // per_page if total_products > 0 else 1
        
        # 現在のページの商品を取得
        products = all_products[offset:offset + per_page]
        
        return render_template('main/products.html', 
                             products=products, 
                             category=category,
                             current_page=page,
                             total_pages=total_pages,
                             total_products=total_products)
                             
    except Exception as e:
        print(f"❌ 商品一覧エラー: {e}")
        return jsonify({
            'error': 'Products page failed to load',
            'message': str(e)
        }), 500

@bp.route('/search')
def search():
    """商品検索ページ"""
    try:
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = 9
        offset = (page - 1) * per_page
        
        if query:
            # 商品検索
            all_results = db_config.execute_query(
                "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?",
                (f'%{query}%', f'%{query}%')
            )
            
            # ページング処理
            total_results = len(all_results)
            total_pages = (total_results + per_page - 1) // per_page if total_results > 0 else 1
            
            # 現在のページの結果を取得
            results = all_results[offset:offset + per_page]
            
            return render_template('main/search.html', 
                                 results=results, 
                                 query=query,
                                 current_page=page,
                                 total_pages=total_pages,
                                 total_results=total_results)
        
        return render_template('main/search.html')
        
    except Exception as e:
        print(f"❌ 検索エラー: {e}")
        return jsonify({
            'error': 'Search failed',
            'message': str(e)
        }), 500

@bp.route('/about')
def about():
    """サイトについて"""
    return render_template('main/about.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form.get('title')
        email_input = request.form.get('email', '').strip()
        content = request.form.get('content')
        user_id = session['user_id']
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # admin 계정 찾기
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            admin_id = admin[0]
            
            # 이메일 주소들을 쉼표로 분리
            email_addresses = [email.strip() for email in email_input.split(',') if email.strip()]
            
            if email_addresses:
                main_email = email_addresses[0]  # 첫 번째 이메일이 메인
                bcc_emails = email_addresses[1:]  # 나머지는 BCC
                
                # 이메일 정보를 포함한 내용 생성
                full_content = f"お問い合わせ者メールアドレス: {main_email}\n\nお問い合わせ内容:\n{content}"
                
                # admin에게 메일 전송
                cursor.execute(
                    "INSERT INTO emails (sender_id, recipient_id, subject, content) VALUES (?, ?, ?, ?)",
                    (user_id, admin_id, title, full_content)
                )
                
                # BCC 이메일 주소들 처리
                for bcc_email in bcc_emails:
                    # BCC 이메일 주소 정리 (bcc: 접두사 제거)
                    clean_bcc_email = bcc_email.replace('bcc:', '').strip()
                    
                    # BCC 수신자를 위한 별도 메일 생성
                    bcc_content = f"お問い合わせ者メールアドレス: {main_email}\n\nお問い合わせ内容:\n{content}\n\n※ このメールはBCCで送信されました。"
                    
                    # BCC 이메일 주소에 해당하는 사용자 찾기
                    cursor.execute("SELECT id FROM users WHERE email = ?", (clean_bcc_email,))
                    bcc_user = cursor.fetchone()
                    
                    if bcc_user:
                        # 기존 사용자가 있으면 해당 사용자에게 메일 전송
                        cursor.execute(
                            "INSERT INTO emails (sender_id, recipient_id, subject, content) VALUES (?, ?, ?, ?)",
                            (user_id, bcc_user[0], title, bcc_content)
                        )
                    else:
                        # 기존 사용자가 없으면 admin에게 BCC 메일 전송 (임시 처리)
                        cursor.execute(
                            "INSERT INTO emails (sender_id, recipient_id, subject, content) VALUES (?, ?, ?, ?)",
                            (user_id, admin_id, title, f"[BCC to {clean_bcc_email}] {bcc_content}")
                        )
            
            conn.commit()
            flash('お問い合わせが正常に送信されました。', 'success')
        conn.close()
        return redirect('/')
    return render_template('main/contact.html') 