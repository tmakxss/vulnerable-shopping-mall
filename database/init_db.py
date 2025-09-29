import sqlite3
import os

def init_database():
    # データベースディレクトリ作成
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect('database/shop.db')
    cursor = conn.cursor()
    
    # ユーザーテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            address TEXT,
            phone TEXT,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 商品テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # カートテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # 注文テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 注文アイテムテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # レビューテーブル (XSSテスト用)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # メールテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (recipient_id) REFERENCES users (id)
        )
    ''')
    
    # メール添付ファイルテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails (id)
        )
    ''')
    
    # 基本データ挿入
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)", 
                  ('admin', 'admin123', 'admin@shop.com', 1))
    
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)", 
                  ('user1', 'password123', 'user1@test.com'))
    
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)", 
                  ('test', 'test123', 'test@test.com'))
    
    # サンプル商品 (実際の商品画像を使用)
    products = [
        ('ノートパソコン', '高性能ノートパソコンです', 120000, 10, '電子機器', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop'),
        ('スマートフォン', '最新スマートフォンです', 80000, 15, '電子機器', 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop'),
        ('ヘッドフォン', '高音質ヘッドフォンです', 15000, 20, '電子機器', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop'),
        ('デスク', '快適なデスクです', 20000, 5, '家具', 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop'),
        ('椅子', '人間工学に基づいた椅子です', 30000, 8, '家具', 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=400&h=300&fit=crop'),
        ('本棚', '整理整頓に便利な本棚です', 15000, 12, '家具', 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop'),
        ('時計', 'シンプルで美しい時計です', 5000, 25, '雑貨', 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=300&fit=crop'),
        ('カバン', '実用的なカバンです', 8000, 18, '雑貨', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop'),
        ('タブレット', '軽量で持ち運びやすいタブレットです', 60000, 12, '電子機器', 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=300&fit=crop'),
        ('キーボード', '静音設計のメカニカルキーボードです', 12000, 30, '電子機器', 'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400&h=300&fit=crop'),
        ('マウス', '高精度光学センサー搭載マウスです', 3000, 40, '電子機器', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=300&fit=crop'),
        ('モニター', '27インチ4Kディスプレイです', 45000, 6, '電子機器', 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop'),
        ('ソファ', '快適なリビングソファです', 80000, 3, '家具', 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop'),
        ('テーブル', 'シンプルなダイニングテーブルです', 25000, 7, '家具', 'https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=400&h=300&fit=crop'),
        ('ベッド', '快眠をサポートするベッドです', 120000, 4, '家具', 'https://images.unsplash.com/photo-1505693314120-0d443867891c?w=400&h=300&fit=crop'),
        ('ランプ', 'LED調光機能付きデスクランプです', 8000, 15, '家具', 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=300&fit=crop'),
        ('カメラ', '高画質デジタルカメラです', 35000, 8, '電子機器', 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400&h=300&fit=crop'),
        ('スピーカー', '高音質ワイヤレススピーカーです', 18000, 10, '電子機器', 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop'),
        ('腕時計', 'スマートウォッチです', 25000, 12, '雑貨', 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop'),
        ('財布', '本革製の高級財布です', 15000, 20, '雑貨', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop'),
        ('傘', '折りたたみ式の軽量傘です', 3000, 50, '雑貨', 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=300&fit=crop'),
        ('マグカップ', '保温性の高いマグカップです', 2000, 35, '雑貨', 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop'),
        ('ノート', '高品質の手帳です', 1500, 60, '雑貨', 'https://images.unsplash.com/photo-1531346680769-a1d79b57de5c?w=400&h=300&fit=crop'),
        ('ペン', '滑らかに書けるボールペンです', 500, 100, '雑貨', 'https://images.unsplash.com/photo-1583485088034-697b5bc36b35?w=400&h=300&fit=crop'),
        ('マスク', '使い捨てマスク100枚入りです', 1000, 80, '雑貨', 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=300&fit=crop'),
        ('ハンガー', 'プラスチック製のハンガーです', 800, 45, '雑貨', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop'),
    ]
    
    for product in products:
        cursor.execute("INSERT OR IGNORE INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)", product)
    
    # サンプルレビュー (XSSテスト用)
    reviews = [
        (1, 2, 5, 'とても良い商品です！'),
        (2, 2, 4, '期待通りの品質でした'),
        (3, 2, 3, '普通の商品です'),
    ]
    
    for review in reviews:
        cursor.execute("INSERT OR IGNORE INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)", review)
    
    conn.commit()
    conn.close()
    
    print("✅ データベース初期化完了")
    print("📊 サンプルデータ挿入完了")

if __name__ == '__main__':
    init_database() 