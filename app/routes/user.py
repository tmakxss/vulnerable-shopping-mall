from flask import Blueprint, render_template, request, session, redirect, flash, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

bp = Blueprint('user', __name__)

# アップロード設定 (脆弱性テスト用)
UPLOAD_FOLDER = 'app/static/uploads/profiles'
# 危険な拡張子も許可 (脆弱性テスト用)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'php', 'jsp', 'asp', 'exe', 'bat', 'sh', 'txt', 'html', 'js'}

def allowed_file(filename):
    # 脆弱性: 拡張子チェックを無効化
    return True  # すべてのファイルを許可

@bp.route('/user/profile')
def user_profile():
    """ユーザープロフィール"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # SQLインジェクション脆弱性
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    conn.close()
    
    return render_template('user/profile.html', user=user)

@bp.route('/user/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """プロフィール編集"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        user_id = session['user_id']
        email = request.form.get('email')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        # プロフィール画像アップロード処理 (脆弱性あり)
        profile_image = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                # 脆弱性: ファイル名のサニタイズを無効化
                filename = file.filename  # secure_filename()を使用しない
                
                # 脆弱性: パストラバーサル攻撃が可能
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                # ディレクトリが存在しない場合は作成
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # 脆弱性: ファイルサイズ制限なし
                file.save(filepath)
                profile_image = f"uploads/profiles/{filename}"
                
                flash(f'ファイル {filename} をアップロードしました', 'success')
        
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # プロフィール画像がある場合のみ更新
        if profile_image:
            cursor.execute("UPDATE users SET email = ?, address = ?, phone = ?, profile_image = ? WHERE id = ?", 
                          (email, address, phone, profile_image, user_id))
        else:
            cursor.execute("UPDATE users SET email = ?, address = ?, phone = ? WHERE id = ?", 
                          (email, address, phone, user_id))
        
        conn.commit()
        conn.close()
        
        flash('プロフィールを更新しました', 'success')
        return redirect('/user/profile')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    conn.close()
    
    return render_template('user/edit_profile.html', user=user)

# 脆弱性: 任意のファイルダウンロードが可能
@bp.route('/uploads/profiles/<filename>')
def download_file(filename):
    """ファイルダウンロード (脆弱性あり)"""
    # 脆弱性: パストラバーサル攻撃が可能
    file_path = os.path.join('app/static/uploads/profiles', filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 脆弱性: Content-Typeを適切に設定しない
        return content, 200, {'Content-Type': 'application/octet-stream'}
    else:
        flash('ファイルが見つかりません', 'error')
        return redirect('/user/profile')

@bp.route('/user/password/change', methods=['GET', 'POST'])
def change_password():
    """パスワード変更"""
    if 'user_id' not in session:
        flash('ログインが必要です', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        user_id = session['user_id']
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 入力検証
        if not current_password or not new_password or not confirm_password:
            flash('すべての項目を入力してください', 'error')
            return render_template('user/change_password.html')
        
        if new_password != confirm_password:
            flash('新しいパスワードが一致しません', 'error')
            return render_template('user/change_password.html')
        
        if len(new_password) < 6:
            flash('パスワードは6文字以上で入力してください', 'error')
            return render_template('user/change_password.html')
        
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # 現在のパスワード確認
        cursor.execute(f"SELECT password FROM users WHERE id = {user_id}")
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            flash('ユーザーが見つかりません', 'error')
            return render_template('user/change_password.html')
        
        # 脆弱性: 平文パスワード比較
        if user[0] != current_password:
            conn.close()
            flash('現在のパスワードが正しくありません', 'error')
            return render_template('user/change_password.html')
        
        # パスワード更新
        cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE id = {user_id}")
        conn.commit()
        conn.close()
        
        flash('パスワードを変更しました', 'success')
        return redirect('/user/profile')
    
    return render_template('user/change_password.html') 