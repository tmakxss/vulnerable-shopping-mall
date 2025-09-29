from flask import Blueprint, request, render_template, session, redirect, flash, send_file
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename

bp = Blueprint('mail', __name__)

# 脆弱な設定 (学習用)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'attachments')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'php', 'jsp', 'asp', 'exe', 'bat', 'sh'}

def allowed_file(filename):
    # 脆弱性: すべてのファイルを許可
    return True

@bp.route('/mail/compose', methods=['GET', 'POST'])
def compose_mail():
    """メール作成 (添付ファイル含む)"""
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        recipient_username = request.form.get('recipient')
        subject = request.form.get('subject')
        content = request.form.get('content')
        
        conn = None
        try:
            conn = sqlite3.connect('database/shop.db')
            cursor = conn.cursor()
            
            # 受信者を探す
            cursor.execute("SELECT id FROM users WHERE username = ?", (recipient_username,))
            recipient = cursor.fetchone()
            
            if recipient:
                # メールを保存
                cursor.execute("""
                    INSERT INTO emails (sender_id, recipient_id, subject, content) 
                    VALUES (?, ?, ?, ?)
                """, (session['user_id'], recipient[0], subject, content))
                
                email_id = cursor.lastrowid
                # email_id = cursor.recipient 
                
                # 添付ファイル処理 (脆弱性含む)
                if 'attachments' in request.files:
                    files = request.files.getlist('attachments')
                    
                    for file in files:
                        if file and file.filename != '':
                            # 脆弱性: ファイル名検証なし
                            original_filename = file.filename
                            stored_filename = f"{uuid.uuid4()}_{original_filename}"
                            
                            # 脆弱性: Directory Traversal可能
                            file_path = os.path.join(UPLOAD_FOLDER, stored_filename)
                            
                            # ディレクトリ作成
                            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            
                            # ファイル保存
                            file.save(file_path)
                            
                            # データベースに添付ファイル情報を保存
                            cursor.execute("""
                                INSERT INTO email_attachments 
                                (email_id, original_filename, stored_filename, file_path, file_size, mime_type) 
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (email_id, original_filename, stored_filename, file_path, 
                                  os.path.getsize(file_path), file.content_type))
                
                conn.commit()
                flash('メールを送信しました', 'success')
                return redirect('/mail/inbox')
            else:
                flash('受信者が見つかりません', 'error')
        except Exception as e:
            flash(f'メールの送信中にエラーが発生しました: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()
    
    return render_template('mail/compose.html')

@bp.route('/mail/inbox')
def inbox():
    """受信メールボックス"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = None
    try:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # 受信メールを取得 (添付ファイル数含む)
        cursor.execute("""
            SELECT e.*, u.username as sender_name,
                   (SELECT COUNT(*) FROM email_attachments WHERE email_id = e.id) as attachment_count
            FROM emails e 
            JOIN users u ON e.sender_id = u.id 
            WHERE e.recipient_id = ? 
            ORDER BY e.created_at DESC
        """, (user_id,))
        
        emails = cursor.fetchall()
        return render_template('mail/inbox.html', emails=emails)
    except Exception as e:
        flash(f'メールボックスのロード中にエラーが発生しました: {str(e)}', 'error')
        return redirect('/')
    finally:
        if conn:
            conn.close()

@bp.route('/mail/sent')
def sent_mail():
    """送信メールボックス"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = None
    try:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # 送信メールを取得 (添付ファイル数含む)
        cursor.execute("""
            SELECT e.*, u.username as recipient_name,
                   (SELECT COUNT(*) FROM email_attachments WHERE email_id = e.id) as attachment_count
            FROM emails e 
            JOIN users u ON e.recipient_id = u.id 
            WHERE e.sender_id = ? 
            ORDER BY e.created_at DESC
        """, (user_id,))
        
        emails = cursor.fetchall()
        return render_template('mail/sent.html', emails=emails)
    except Exception as e:
        flash(f'送信メールボックスのロード中にエラーが発生しました: {str(e)}', 'error')
        return redirect('/')
    finally:
        if conn:
            conn.close()

@bp.route('/mail/read/<int:email_id>')
def read_mail(email_id):
    """メール読み取り (添付ファイル含む)"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = None
    try:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # メールを取得
        cursor.execute("""
            SELECT e.*, u.username as sender_name
            FROM emails e 
            JOIN users u ON e.sender_id = u.id 
            WHERE e.id = ? AND (e.recipient_id = ? OR e.sender_id = ?)
        """, (email_id, user_id, user_id))
        
        email = cursor.fetchone()
        
        if email:
            # 添付ファイルを取得
            cursor.execute("""
                SELECT * FROM email_attachments WHERE email_id = ?
            """, (email_id,))
            
            attachments = cursor.fetchall()
            
            # 既読マーク (受信者の場合)
            if email[2] == user_id:  # recipient_id
                cursor.execute("UPDATE emails SET is_read = 1 WHERE id = ?", (email_id,))
                conn.commit()
            
            return render_template('mail/read.html', email=email, attachments=attachments)
        else:
            flash('メールが見つかりません', 'error')
            return redirect('/mail/inbox')
    except Exception as e:
        flash(f'メールの読み取り中にエラーが発生しました: {str(e)}', 'error')
        return redirect('/mail/inbox')
    finally:
        if conn:
            conn.close()

@bp.route('/mail/attachment/<int:attachment_id>')
def download_attachment(attachment_id):
    """添付ファイルダウンロード (脆弱性含む)"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = None
    try:
        conn = sqlite3.connect('database/shop.db')
        cursor = conn.cursor()
        
        # 添付ファイル情報を取得
        cursor.execute("""
            SELECT ea.*, e.sender_id, e.recipient_id 
            FROM email_attachments ea
            JOIN emails e ON ea.email_id = e.id
            WHERE ea.id = ?
        """, (attachment_id,))
        
        attachment = cursor.fetchone()
        
        if attachment and (attachment[8] == user_id or attachment[9] == user_id):
            # 脆弱性: ファイルパス検証なし
            file_path = attachment[4]  # file_path
            
            if os.path.exists(file_path):
                return send_file(file_path, 
                               as_attachment=True,
                               download_name=attachment[2])  # original_filename
            else:
                flash('ファイルが見つかりません', 'error')
        else:
            flash('権限がありません', 'error')
        
        return redirect('/mail/inbox')
    except Exception as e:
        flash(f'添付ファイルのダウンロード中にエラーが発生しました: {str(e)}', 'error')
        return redirect('/mail/inbox')
    finally:
        if conn:
            conn.close() 