from flask import Blueprint, render_template, request, session, redirect, flash
import sqlite3

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """メインページ"""
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # 人気商品を取得
    cursor.execute("SELECT * FROM products ORDER BY id DESC LIMIT 4")
    featured_products = cursor.fetchall()
    
    # レビュー検索機能
    review_query = request.args.get('review_search', '')
    recent_reviews = []
    
    if review_query:
        # レビュー検索 (SQLインジェクション対策済み、XSS脆弱性は残存)
        cursor.execute("""
            SELECT r.*, u.username, p.name as product_name, p.image_url 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            JOIN products p ON r.product_id = p.id 
            WHERE r.comment LIKE ? OR u.username LIKE ? OR p.name LIKE ?
            ORDER BY r.created_at DESC LIMIT 10
        """, (f'%{review_query}%', f'%{review_query}%', f'%{review_query}%'))
        recent_reviews = cursor.fetchall()
    else:
        # 最新レビューを取得
        cursor.execute("""
            SELECT r.*, u.username, p.name as product_name, p.image_url 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            JOIN products p ON r.product_id = p.id 
            ORDER BY r.created_at DESC LIMIT 10
        """)
        recent_reviews = cursor.fetchall()
    
    conn.close()
    
    return render_template('main/index.html', 
                         featured_products=featured_products, 
                         recent_reviews=recent_reviews,
                         review_query=review_query)

@bp.route('/products')
def products():
    """商品一覧ページ"""
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    if category:
        # SQLインジェクション脆弱性
        query = f"SELECT * FROM products WHERE category = '{category}'"
        cursor.execute(query)
    else:
        cursor.execute("SELECT * FROM products")
    
    all_products = cursor.fetchall()
    
    # ページング処理
    total_products = len(all_products)
    total_pages = (total_products + per_page - 1) // per_page
    
    # 現在のページの商品を取得
    products = all_products[offset:offset + per_page]
    
    conn.close()
    
    return render_template('main/products.html', 
                         products=products, 
                         category=category,
                         current_page=page,
                         total_pages=total_pages,
                         total_products=total_products)

@bp.route('/search')
def search():
    """商品検索ページ"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 9
    offset = (page - 1) * per_page
    
    if query:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # SQLインジェクション脆弱性
        sql_query = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
        cursor.execute(sql_query)
        all_results = cursor.fetchall()
        
        # ページング処理
        total_results = len(all_results)
        total_pages = (total_results + per_page - 1) // per_page
        
        # 現在のページの結果を取得
        results = all_results[offset:offset + per_page]
        
        conn.close()
        
        return render_template('main/search.html', 
                             results=results, 
                             query=query,
                             current_page=page,
                             total_pages=total_pages,
                             total_results=total_results)
    
    return render_template('main/search.html')

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