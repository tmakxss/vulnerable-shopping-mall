from flask import Blueprint, render_template, request, session, redirect, flash
import sqlite3

bp = Blueprint('product', __name__)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """商品詳細ページ"""
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # SQLインジェクション脆弱性
    cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        flash('商品が見つかりません', 'error')
        return redirect('/products')
    
    # レビュー取得 (XSS脆弱性)
    cursor.execute(f"SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = {product_id} ORDER BY r.created_at DESC")
    reviews = cursor.fetchall()
    
    conn.close()
    
    return render_template('product/detail.html', product=product, reviews=reviews)

@bp.route('/product/<int:product_id>/review', methods=['POST'])
def add_review(product_id):
    """レビュー投稿"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    user_id = session['user_id']
    
    if not rating or not comment:
        flash('評価とコメントを入力してください', 'error')
        return redirect(f'/product/{product_id}')
    
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # XSS脆弱性 - コメント内容をフィルタリングせずに保存
    cursor.execute("INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)", 
                  (product_id, user_id, rating, comment))
    conn.commit()
    conn.close()
    
    flash('レビューを投稿しました', 'success')
    return redirect(f'/product/{product_id}')

@bp.route('/categories')
def categories():
    """カテゴリ一覧"""
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()
    conn.close()
    
    return render_template('product/categories.html', categories=categories) 