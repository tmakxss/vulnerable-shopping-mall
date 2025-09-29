from flask import Blueprint, render_template, request, session, redirect, flash
import sqlite3

bp = Blueprint('review', __name__)

@bp.route('/reviews')
def all_reviews():
    """全レビュー一覧"""
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # XSS脆弱性のあるレビュー表示
    cursor.execute("""
        SELECT r.*, u.username, p.name as product_name, p.image_url 
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        JOIN products p ON r.product_id = p.id 
        ORDER BY r.created_at DESC
    """)
    reviews = cursor.fetchall()
    conn.close()
    
    return render_template('review/list.html', reviews=reviews)

@bp.route('/review/<int:review_id>')
def review_detail(review_id):
    """レビュー詳細"""
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # SQLインジェクション脆弱性
    cursor.execute(f"SELECT r.*, u.username, p.name as product_name, p.image_url FROM reviews r JOIN users u ON r.user_id = u.id JOIN products p ON r.product_id = p.id WHERE r.id = {review_id}")
    review = cursor.fetchone()
    conn.close()
    
    if not review:
        flash('レビューが見つかりません', 'error')
        return redirect('/reviews')
    
    return render_template('review/detail.html', review=review) 