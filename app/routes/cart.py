from flask import Blueprint, render_template, request, session, redirect, flash
import sqlite3

bp = Blueprint('cart', __name__)

@bp.route('/cart')
def view_cart():
    """カート表示"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, p.name, p.price, c.quantity, p.id as product_id, p.image_url
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = ?
    """, (user_id,))
    
    cart_items = cursor.fetchall()
    conn.close()
    
    total = sum(item[2] * item[3] for item in cart_items)
    
    return render_template('cart/view.html', cart_items=cart_items, total=total)

@bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """カートに商品追加"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1)
    user_id = session['user_id']
    
    # CSRFトークン検証なし - 脆弱性
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # 既存のカートアイテム確認
    cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", 
                  (user_id, product_id))
    existing = cursor.fetchone()
    
    if existing:
        # 数量更新
        cursor.execute("UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?", 
                      (quantity, user_id, product_id))
    else:
        # 新規アイテム追加
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", 
                      (user_id, product_id, quantity))
    
    conn.commit()
    conn.close()
    
    flash('カートに追加しました', 'success')
    return redirect('/cart')

@bp.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    """カートから商品削除"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    # CSRFトークン検証なし
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM cart WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()
    
    flash('カートから削除しました', 'success')
    return redirect('/cart')

@bp.route('/cart/update', methods=['POST'])
def update_cart():
    """カート数量更新"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # 隠しフィールド操作脆弱性
    item_id = request.form.get('item_id')
    quantity = request.form.get('quantity')
    
    cursor.execute("UPDATE cart SET quantity = ? WHERE id = ? AND user_id = ?", 
                  (quantity, item_id, user_id))
    conn.commit()
    conn.close()
    
    flash('カートを更新しました', 'success')
    return redirect('/cart') 