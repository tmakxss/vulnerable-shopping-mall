from flask import Blueprint, render_template, request, session, redirect, flash, jsonify
from app.database import db_config

bp = Blueprint('product', __name__)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """商品詳細ページ"""
    try:
        # 商品情報取得
        products = db_config.execute_query(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        
        if not products:
            flash('商品が見つかりません', 'error')
            return redirect('/products')
            
        product = products[0]
        
        # レビュー取得 (XSS脆弱性は学習用に残す)
        reviews = db_config.execute_query(
            "SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = ? ORDER BY r.created_at DESC",
            (product_id,)
        )
        
        # HTMLテンプレートが見つからない場合のフォールバック
        try:
            return render_template('product/detail.html', product=product, reviews=reviews)
        except Exception as template_error:
            print(f"❌ テンプレートエラー: {template_error}")
            # JSONレスポンスでフォールバック
            return jsonify({
                'page': 'Product Detail',
                'product': product,
                'reviews': reviews,
                'mode': 'JSON API (テンプレートフォールバック)'
            })
        
    except Exception as e:
        print(f"❌ 商品詳細エラー: {e}")
        return jsonify({
            'error': 'Product detail failed to load',
            'message': str(e)
        }), 500

@bp.route('/product/<int:product_id>/review', methods=['POST'])
def add_review(product_id):
    """レビュー投稿"""
    try:
        if 'user_id' not in session:
            flash('ログインが必要です', 'error')
            return redirect('/login')
        
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        user_id = session['user_id']
        
        if not rating or not comment:
            flash('評価とコメントを入力してください', 'error')
            return redirect(f'/product/{product_id}')
        
        # XSS脆弱性 - コメント内容をフィルタリングせずに保存（学習用）
        result = db_config.execute_update(
            "INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)", 
            (product_id, user_id, rating, comment)
        )
        
        if result:
            flash('レビューを投稿しました', 'success')
        else:
            flash('レビュー投稿に失敗しました', 'error')
            
        return redirect(f'/product/{product_id}')
        
    except Exception as e:
        print(f"❌ レビュー投稿エラー: {e}")
        flash('エラーが発生しました', 'error')
        return redirect(f'/product/{product_id}')

@bp.route('/categories')
def categories():
    """カテゴリ一覧"""
    try:
        categories = db_config.execute_query("SELECT DISTINCT category FROM products")
        
        # カテゴリごとの商品数も取得
        category_counts = {}
        for cat in categories:
            category_name = cat['category']
            count = db_config.execute_query(
                "SELECT COUNT(*) as count FROM products WHERE category = ?",
                (category_name,)
            )
            category_counts[category_name] = count[0]['count'] if count else 0
            
        return render_template('product/categories.html', 
                             categories=categories,
                             category_counts=category_counts)
                             
    except Exception as e:
        print(f"❌ カテゴリ一覧エラー: {e}")
        return jsonify({
            'error': 'Categories failed to load',
            'message': str(e)
        }), 500
    
    return render_template('product/categories.html', categories=categories) 