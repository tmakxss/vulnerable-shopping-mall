from flask import Blueprint, render_template, request, session, redirect, flash
import sqlite3

bp = Blueprint('order', __name__)

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """チェックアウトページ"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        user_id = session['user_id']
        
        # 注文情報 (隠しフィールド操作脆弱性)
        shipping_address = request.form.get('shipping_address')
        payment_method = request.form.get('payment_method')
        total_amount = request.form.get('total_amount')  # 隠しフィールド
        
        if not shipping_address or not payment_method:
            flash('配送先住所と支払い方法を入力してください', 'error')
            return redirect('/checkout')
        
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # 注文作成
        cursor.execute("""
            INSERT INTO orders (user_id, shipping_address, payment_method, total_amount, status, created_at) 
            VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (user_id, shipping_address, payment_method, total_amount))
        
        order_id = cursor.lastrowid
        
        # カートアイテムを注文アイテムに移動
        cursor.execute("SELECT product_id, quantity FROM cart WHERE user_id = ?", (user_id,))
        cart_items = cursor.fetchall()
        
        for item in cart_items:
            # 商品価格取得
            cursor.execute("SELECT price FROM products WHERE id = ?", (item[0],))
            price = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price) 
                VALUES (?, ?, ?, ?)
            """, (order_id, item[0], item[1], price))
        
        # カートを空にする
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        flash('注文が完了しました', 'success')
        return redirect(f'/order/{order_id}')
    
    # カート情報表示
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.name, p.price, c.quantity, (p.price * c.quantity) as total
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = ?
    """, (user_id,))
    
    cart_items = cursor.fetchall()
    total = sum(item[3] for item in cart_items)
    conn.close()
    
    if not cart_items:
        flash('カートが空です', 'error')
        return redirect('/cart')
    
    return render_template('order/checkout.html', cart_items=cart_items, total=total)

@bp.route('/order/<int:order_id>')
def order_detail(order_id):
    """注文詳細ページ"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # SQLインジェクション脆弱性 - 注文照会
    cursor.execute(f"SELECT * FROM orders WHERE id = {order_id} AND user_id = {user_id}")
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        flash('注文が見つかりません', 'error')
        return redirect('/orders')
    
    # 注文アイテム照会
    cursor.execute(f"SELECT oi.*, p.name, p.price FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = {order_id}")
    items = cursor.fetchall()
    conn.close()
    
    return render_template('order/detail.html', order=order, items=items)

@bp.route('/orders')
def my_orders():
    """注文履歴"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # SQLインジェクション脆弱性
    cursor.execute(f"SELECT * FROM orders WHERE user_id = {user_id} ORDER BY id ASC")
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('order/list.html', orders=orders)

@bp.route('/order/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    """주문 취소"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    # 본인 주문만 취소 가능
    cursor.execute("SELECT status FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
    order = cursor.fetchone()
    if not order:
        conn.close()
        flash('注文が見つかりません', 'error')
        return redirect('/orders')
    if order[0] != 'pending':
        conn.close()
        flash('すでに処理された注文はキャンセルできません', 'error')
        return redirect('/orders')
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    flash('ご注文がキャンセルされました', 'success')
    return redirect('/orders') 