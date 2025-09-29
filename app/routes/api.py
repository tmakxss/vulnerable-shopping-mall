from flask import Blueprint, request, jsonify
import sqlite3
import subprocess
import os

bp = Blueprint('api', __name__)

@bp.route('/api/products')
def api_products():
    """商品API"""
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    category = request.args.get('category', '')
    
    if category:
        # SQLインジェクション脆弱性
        cursor.execute(f"SELECT * FROM products WHERE category = '{category}'")
    else:
        cursor.execute("SELECT * FROM products")
    
    products = cursor.fetchall()
    conn.close()
    
    # 商品データを辞書形式に変換
    product_list = []
    for product in products:
        product_list.append({
            'id': product[0],
            'name': product[1],
            'description': product[2],
            'price': product[3],
            'stock': product[4],
            'category': product[5]
        })
    
    return jsonify(product_list)

@bp.route('/api/ping', methods=['POST'])
def api_ping():
    """Ping API (OS Command Injection脆弱性)"""
    data = request.get_json()
    host = data.get('host', '127.0.0.1')
    
    try:
        # OS Command Injection脆弱性
        result = subprocess.check_output(f"ping -c 4 {host}", shell=True, text=True)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/system', methods=['POST'])
def api_system():
    """システムコマンドAPI (非常に危険)"""
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'success': False, 'error': 'コマンドが指定されていません'})
    
    try:
        # 非常に危険なコマンド実行
        result = subprocess.check_output(command, shell=True, text=True)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/file/<path:filename>')
def api_file(filename):
    """ファイルアクセスAPI (Directory Traversal脆弱性)"""
    # ディレクトリトラバーサル脆弱性
    file_path = os.path.join('app/static', filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return jsonify({'success': True, 'content': content})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'ファイルが見つかりません'}) 