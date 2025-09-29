from flask import Blueprint, render_template, request, session, redirect, flash, jsonify, make_response
import sqlite3
import os
import subprocess
import pickle
import base64
import json
import shutil
from datetime import datetime

bp = Blueprint('admin', __name__)

@bp.route('/admin')
def admin_dashboard():
    """管理者ダッシュボード"""
    # 脆弱な権限検証
    user_id = request.cookies.get('user_id')
    is_admin = request.cookies.get('is_admin', '0')
    role = request.cookies.get('role', 'user')
    
    # 権限検証 (隠しパラメータによる権限昇格脆弱性デモ)
    if int(is_admin) > 0:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # 統計情報
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reviews")
        review_count = cursor.fetchone()[0]
        
        conn.close()
        
        return render_template('admin/dashboard.html', 
                             user_count=user_count,
                             order_count=order_count,
                             product_count=product_count,
                             review_count=review_count,
                             current_role=role,
                             is_admin=is_admin)
    else:
        return "管理者権限が必要です"

@bp.route('/admin/users')
def admin_users():
    """ユーザー管理"""
    is_admin = request.cookies.get('is_admin', '0')
    
    if int(is_admin) > 0:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        if search:
            cursor.execute(f"SELECT ROW_NUMBER() OVER (ORDER BY created_at ASC) as row_num, * FROM users WHERE username LIKE '%{search}%' OR email LIKE '%{search}%'")
        else:
            cursor.execute("SELECT ROW_NUMBER() OVER (ORDER BY created_at ASC) as row_num, * FROM users ORDER BY created_at ASC")
        
        all_users = cursor.fetchall()
        
        # ページング計算
        total = len(all_users)
        total_pages = (total + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        users = all_users[start_idx:end_idx]
        
        conn.close()
        
        return render_template('admin/users.html', 
                             users=users, 
                             search=search, 
                             page=page, 
                             total_pages=total_pages,
                             total=total)
    
    return "管理者権限が必要です"

@bp.route('/admin/users/delete/<int:user_id>')
def delete_user(user_id):
    """ユーザー削除"""
    is_admin = request.cookies.get('is_admin', '0')
    
    if int(is_admin) > 0:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        flash('ユーザーを削除しました', 'success')
        return redirect('/admin/users')
    
    return "管理者権限が必要です"

@bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    """ユーザー編集"""
    is_admin = request.cookies.get('is_admin', '0')
    
    if int(is_admin) > 0:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            address = request.form.get('address')
            phone = request.form.get('phone')
            is_admin = request.form.get('is_admin') == 'on'
            new_password = request.form.get('new_password')
            
            if new_password:
                cursor.execute("UPDATE users SET username=?, email=?, address=?, phone=?, is_admin=?, password=? WHERE id=?",
                             (username, email, address, phone, is_admin, new_password, user_id))
            else:
                cursor.execute("UPDATE users SET username=?, email=?, address=?, phone=?, is_admin=? WHERE id=?",
                             (username, email, address, phone, is_admin, user_id))
            
            conn.commit()
            conn.close()
            
            flash('ユーザーを更新しました', 'success')
            return redirect('/admin/users')
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return render_template('admin/edit_user.html', user=user)
        else:
            flash('ユーザーが見つかりません', 'danger')
            return redirect('/admin/users')
    
    return "管理者権限が必要です"

@bp.route('/admin/orders')
def admin_orders():
    """注文管理"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        if search:
            cursor.execute(f"SELECT ROW_NUMBER() OVER (ORDER BY o.id ASC) as row_num, o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id LIKE '%{search}%' OR u.username LIKE '%{search}%' ORDER BY o.id ASC")
        else:
            cursor.execute("SELECT ROW_NUMBER() OVER (ORDER BY o.id ASC) as row_num, o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.id ASC")
        
        all_orders = cursor.fetchall()
        
        # ページング計算
        total = len(all_orders)
        total_pages = (total + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        orders = all_orders[start_idx:end_idx]
        
        conn.close()
        
        return render_template('admin/orders.html', 
                             orders=orders, 
                             search=search, 
                             page=page, 
                             total_pages=total_pages,
                             total=total)
    
    return "管理者権限が必要です"

@bp.route('/admin/orders/edit/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    """注文編集"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        if request.method == 'POST':
            shipping_address = request.form.get('shipping_address')
            payment_method = request.form.get('payment_method')
            total_amount = request.form.get('total_amount')
            status = request.form.get('status')
            
            cursor.execute("UPDATE orders SET shipping_address=?, payment_method=?, total_amount=?, status=? WHERE id=?",
                         (shipping_address, payment_method, total_amount, status, order_id))
            
            conn.commit()
            conn.close()
            
            flash('注文を更新しました', 'success')
            return redirect('/admin/orders')
        
        cursor.execute("SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id = ?", (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if order:
            return render_template('admin/edit_order.html', order=order)
        else:
            flash('注文が見つかりません', 'danger')
            return redirect('/admin/orders')
    
    return "管理者権限が必要です"

@bp.route('/admin/orders/delete/<int:order_id>')
def delete_order(order_id):
    """注文削除"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        
        flash('注文を削除しました', 'success')
        return redirect('/admin/orders')
    
    return "管理者権限が必要です"

@bp.route('/admin/products')
def admin_products():
    """商品管理"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        if search:
            cursor.execute(f"SELECT ROW_NUMBER() OVER (ORDER BY id ASC) as row_num, * FROM products WHERE name LIKE '%{search}%' OR category LIKE '%{search}%' ORDER BY id ASC")
        else:
            cursor.execute("SELECT ROW_NUMBER() OVER (ORDER BY id ASC) as row_num, * FROM products ORDER BY id ASC")
        
        all_products = cursor.fetchall()
        
        # ページング計算
        total = len(all_products)
        total_pages = (total + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        products = all_products[start_idx:end_idx]
        
        conn.close()
        
        return render_template('admin/products.html', 
                             products=products, 
                             search=search, 
                             page=page, 
                             total_pages=total_pages,
                             total=total)
    
    return "管理者権限が必要です"

@bp.route('/admin/products/delete/<int:product_id>')
def delete_product(product_id):
    """商品削除 - IDOR脆弱性"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # IDOR脆弱性: 権限チェックなしで削除
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        
        flash('商品を削除しました', 'success')
        return redirect('/admin/products')
    
    return "管理者権限が必要です"

@bp.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():
    """商品追加"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            stock = request.form.get('stock')
            category = request.form.get('category')
            
            file = request.files.get('image')
            image_url = ''
            
            if file:
                filename = file.filename
                file_path = os.path.join('app/static/uploads', filename)
                file.save(file_path)
                image_url = f'/static/uploads/{filename}'
            
            conn = sqlite3.connect('database/shop.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                         (name, description, price, stock, category, image_url))
            conn.commit()
            conn.close()
            
            flash('商品を追加しました', 'success')
            return redirect('/admin/products')
        
        return render_template('admin/add_product.html')
    
    return "管理者権限が必要です"

@bp.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """商品編集"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            stock = request.form.get('stock')
            category = request.form.get('category')
            
            file = request.files.get('image')
            
            if file and file.filename:
                filename = file.filename
                file_path = os.path.join('app/static/uploads', filename)
                file.save(file_path)
                image_url = f'/static/uploads/{filename}'
                cursor.execute("UPDATE products SET name=?, description=?, price=?, stock=?, category=?, image_url=? WHERE id=?",
                             (name, description, price, stock, category, image_url, product_id))
            else:
                cursor.execute("UPDATE products SET name=?, description=?, price=?, stock=?, category=? WHERE id=?",
                             (name, description, price, stock, category, product_id))
            
            conn.commit()
            conn.close()
            
            flash('商品を更新しました', 'success')
            return redirect('/admin/products')
        
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()
        
        if product:
            return render_template('admin/edit_product.html', product=product)
        else:
            flash('商品が見つかりません', 'danger')
            return redirect('/admin/products')
    
    return "管理者権限が必要です"

@bp.route('/admin/reviews')
def admin_reviews():
    """レビュー管理"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        if search:
            cursor.execute(f"""
                SELECT ROW_NUMBER() OVER (ORDER BY r.id ASC) as row_num, r.*, u.username, p.name as product_name 
                FROM reviews r 
                JOIN users u ON r.user_id = u.id 
                JOIN products p ON r.product_id = p.id 
                WHERE p.name LIKE '%{search}%' OR u.username LIKE '%{search}%'
                ORDER BY r.id ASC
            """)
        else:
            cursor.execute("""
                SELECT ROW_NUMBER() OVER (ORDER BY r.id ASC) as row_num, r.*, u.username, p.name as product_name 
                FROM reviews r 
                JOIN users u ON r.user_id = u.id 
                JOIN products p ON r.product_id = p.id 
                ORDER BY r.id ASC
            """)
        
        all_reviews = cursor.fetchall()
        
        # ページング計算
        total = len(all_reviews)
        total_pages = (total + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        reviews = all_reviews[start_idx:end_idx]
        
        conn.close()
        
        return render_template('admin/reviews.html', 
                             reviews=reviews, 
                             search=search, 
                             page=page, 
                             total_pages=total_pages,
                             total=total)
    
    return "管理者権限が必要です"

@bp.route('/admin/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    """レビュー編集"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        if request.method == 'POST':
            rating = request.form.get('rating')
            comment = request.form.get('comment')
            
            cursor.execute("UPDATE reviews SET rating=?, comment=? WHERE id=?",
                         (rating, comment, review_id))
            
            conn.commit()
            conn.close()
            
            flash('レビューを更新しました', 'success')
            return redirect('/admin/reviews')
        
        cursor.execute("""
            SELECT ROW_NUMBER() OVER (ORDER BY r.id ASC) as row_num, r.*, u.username, p.name as product_name 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            JOIN products p ON r.product_id = p.id 
            WHERE r.id = ?
        """, (review_id,))
        review = cursor.fetchone()
        conn.close()
        
        if review:
            return render_template('admin/edit_review.html', review=review)
        else:
            flash('レビューが見つかりません', 'danger')
            return redirect('/admin/reviews')
    
    return "管理者権限が必要です"

@bp.route('/admin/reviews/delete/<int:review_id>')
def delete_review(review_id):
    """レビュー削除"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
        conn.close()
        
        flash('レビューを削除しました', 'success')
        return redirect('/admin/reviews')
    
    return "管理者権限が必要です"

@bp.route('/admin/system')
def system_info():
    """システム情報"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':

        system_info = {
            'os': os.name,
            'cwd': os.getcwd(),
            'env': dict(os.environ),
            'files': os.listdir('.')
        }
        
        return render_template('admin/system.html', system_info=system_info)
    
    return "管理者権限が必要です"

@bp.route('/admin/command', methods=['GET', 'POST'])
def execute_command():
    """コマンド実行"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        if request.method == 'POST':
            command = request.form.get('command')
            

            try:
                result = subprocess.check_output(command, shell=True, text=True)
                return render_template('admin/command.html', result=result, command=command)
            except Exception as e:
                return render_template('admin/command.html', result=str(e), command=command)
        
        return render_template('admin/command.html')
    
    return "管理者権限が必要です"

@bp.route('/admin/config')
def view_config():
    """設定表示"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':

        config = {
            'database_path': 'database/shop.db',
            'admin_password': 'admin123',
            'secret_key': 'super_secret_key_123',
            'debug_mode': True
        }
        
        return render_template('admin/config.html', config=config)
    
    return "管理者権限が必要です"

@bp.route('/admin/backup')
def backup_data():
    """データバックアップ"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        backup_path = request.args.get('path', 'backup.db')
        

        try:
            with open(backup_path, 'r') as f:
                content = f.read()
            return f"バックアップファイルの内容: {content}"
        except Exception as e:
            return f"エラー: {str(e)}"
    
    return "管理者権限が必要です"

@bp.route('/admin/deserialize')
def deserialize_data():
    """デシリアライゼーション"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        data = request.args.get('data', '')
        
        if data:
            try:
 
                decoded_data = base64.b64decode(data)
                deserialized = pickle.loads(decoded_data)
                return f"デシリアライズ結果: {deserialized}"
            except Exception as e:
                return f"エラー: {str(e)}"
        
        return render_template('admin/deserialize.html')
    
    return "管理者権限が必要です"

@bp.route('/admin/database/backup', methods=['GET', 'POST'])
def backup_database():
    """データベースバックアップ"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        if request.method == 'POST':
            try:
                # ユーザーが入力したファイル名を取得
                custom_name = request.form.get('backup_name', '').strip()
                
                # ファイル名の検証
                if not custom_name:
                    flash('バックアップ名を入力してください', 'danger')
                    return redirect('/admin/database')
                
                # ファイル名に使用できない文字を除去
                import re
                safe_name = re.sub(r'[^\w\-_\.]', '_', custom_name)
                
                # タイムスタンプを追加
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f'database/backup_{safe_name}_{timestamp}.db'
                
                # データベースファイルをコピー
                shutil.copy2('database/shop.db', backup_path)
                
                flash(f'データベースバックアップが完了しました: {backup_path}', 'success')
                return redirect('/admin/database')
            except Exception as e:
                flash(f'バックアップエラー: {str(e)}', 'danger')
                return redirect('/admin/database')
        
        # GET リクエストの場合はバックアップ作成フォームを表示
        return render_template('admin/backup_form.html')
    
    return "管理者権限が必要です"

@bp.route('/admin/database/restore/<filename>')
def restore_database(filename):
    """データベース復元"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        try:
            backup_path = f'database/{filename}'
            
            # バックアップファイルが存在するかチェック
            if not os.path.exists(backup_path):
                flash('バックアップファイルが見つかりません', 'danger')
                return redirect('/admin/database')
            
            # 現在のデータベースをバックアップ
            current_backup = f'database/current_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2('database/shop.db', current_backup)
            
            # バックアップから復元
            shutil.copy2(backup_path, 'database/shop.db')
            
            flash(f'データベース復元が完了しました: {filename}', 'success')
            return redirect('/admin/database')
        except Exception as e:
            flash(f'復元エラー: {str(e)}', 'danger')
            return redirect('/admin/database')
    
    return "管理者権限が必要です"

@bp.route('/admin/database/reset')
def reset_database():
    """データベース初期化"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        try:
            # 現在のデータベースをバックアップ
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'database/backup_before_reset_{timestamp}.db'
            shutil.copy2('database/shop.db', backup_path)
            
            # データベース初期化スクリプトを実行
            import subprocess
            result = subprocess.run(['python', 'database/init_db.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                flash(f'データベース初期化が完了しました。バックアップ: {backup_path}', 'success')
            else:
                flash(f'初期化エラー: {result.stderr}', 'danger')
            
            return redirect('/admin/database')
        except Exception as e:
            flash(f'初期化エラー: {str(e)}', 'danger')
            return redirect('/admin/database')
    
    return "管理者権限が必要です"

@bp.route('/admin/database')
def database_management():
    """データベース管理"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        import glob
        from datetime import datetime
        
        # バックアップファイル一覧を取得
        backup_files = []
        for backup_file in glob.glob('database/backup_*.db'):
            file_stat = os.stat(backup_file)
            backup_files.append({
                'filename': os.path.basename(backup_file),
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime)
            })
        
        # 作成日時でソート
        backup_files.sort(key=lambda x: x['created'], reverse=True)
        
        return render_template('admin/database.html', backup_files=backup_files)
    
    return "管理者権限が必要です"

@bp.route('/admin/database/delete/<filename>')
def delete_backup(filename):
    """バックアップファイル削除"""
    user_id = request.cookies.get('user_id')
    
    if user_id == '1':
        try:
            backup_path = f'database/{filename}'
            
            # バックアップファイルが存在するかチェック
            if not os.path.exists(backup_path):
                flash('バックアップファイルが見つかりません', 'danger')
                return redirect('/admin/database')
            
            # ファイル削除
            os.remove(backup_path)
            
            flash(f'バックアップファイルを削除しました: {filename}', 'success')
            return redirect('/admin/database')
        except Exception as e:
            flash(f'削除エラー: {str(e)}', 'danger')
            return redirect('/admin/database')
    
    return "管理者権限が必要です"

 