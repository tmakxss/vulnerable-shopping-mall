from flask import Blueprint, request, render_template, redirect, session, flash, make_response
import sqlite3
import json
import base64

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページ"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # 隠しパラメータによる権限変更 (権限昇格脆弱性)
        role = request.form.get('role', 'user')  # デフォルト値は 'user'
        
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # SQLインジェクション脆弱性のあるログイン
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # 隠しパラメータによる権限変更
            is_admin = 0
            if role == 'admin':
                is_admin = 1
            elif role == 'super_admin':
                is_admin = 2  # スーパー管理者権限
            elif role == 'moderator':
                is_admin = 3  # モデレーター権限
            else:
                is_admin = user[6]  # 元の権限を維持
            
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = is_admin
            session['role'] = role  # 役割情報もセッションに保存
            
            # 脆弱なCookie設定
            response = make_response(redirect('/'))
            response.set_cookie('user_id', str(user[0]), max_age=3600)
            response.set_cookie('username', user[1], max_age=3600)
            response.set_cookie('is_admin', str(is_admin), max_age=3600)
            response.set_cookie('role', role, max_age=3600)
            
            # 脆弱なJWT風トークン (Base64エンコード)
            token_data = {
                'user_id': user[0],
                'username': user[1],
                'is_admin': is_admin,
                'role': role
            }
            token = base64.b64encode(json.dumps(token_data).encode()).decode()
            response.set_cookie('auth_token', token, max_age=3600)
            
            flash(f'ログインしました (権限: {role})', 'success')
            return response
        else:
            flash('ユーザー名またはパスワードが正しくありません', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録ページ"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        try:
            # XSS脆弱性のあるユーザー登録
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                          (username, password, email))
            conn.commit()
            flash('ユーザー登録が完了しました', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('このユーザー名は既に使用されています', 'error')
        finally:
            conn.close()
    
    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    """ログアウト"""
    session.clear()
    flash('ログアウトしました', 'success')
    return redirect('/')

@bp.route('/profile')
def profile():
    """ユーザープロフィール"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # SQLインジェクション脆弱性
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    conn.close()
    
    return render_template('auth/profile.html', user=user) 