-- Supabase PostgreSQL用データベース初期化スクリプト
-- このスクリプトをSupabaseのSQL Editorで実行してください

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    phone VARCHAR(255),
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品テーブル
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(255),
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- カートテーブル
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- 注文テーブル
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    shipping_address TEXT NOT NULL,
    payment_method VARCHAR(255) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(255) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- 注文アイテムテーブル
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- レビューテーブル (XSSテスト用)
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- メールテーブル
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    subject VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users (id),
    FOREIGN KEY (recipient_id) REFERENCES users (id)
);

-- メール添付ファイルテーブル
CREATE TABLE IF NOT EXISTS email_attachments (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails (id)
);

-- 基本データ挿入
INSERT INTO users (username, password, email, is_admin) VALUES 
('admin', 'admin123', 'admin@shop.com', true)
ON CONFLICT (username) DO NOTHING;

INSERT INTO users (username, password, email) VALUES 
('user1', 'password123', 'user1@test.com'),
('test', 'test123', 'test@test.com')
ON CONFLICT (username) DO NOTHING;

-- サンプル商品データ
INSERT INTO products (name, description, price, stock, category, image_url) VALUES 
('ノートパソコン', '高性能ノートパソコンです', 120000.00, 10, '電子機器', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop'),
('スマートフォン', '最新スマートフォンです', 80000.00, 15, '電子機器', 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop'),
('ヘッドフォン', '高音質ヘッドフォンです', 15000.00, 20, '電子機器', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop'),
('デスク', '快適なデスクです', 20000.00, 5, '家具', 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop'),
('椅子', '人間工学に基づいた椅子です', 30000.00, 8, '家具', 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=400&h=300&fit=crop'),
('本棚', '整理整頓に便利な本棚です', 15000.00, 12, '家具', 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop'),
('時計', 'シンプルで美しい時計です', 5000.00, 25, '雑貨', 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=300&fit=crop'),
('カバン', '実用的なカバンです', 8000.00, 18, '雑貨', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop'),
('タブレット', '軽量で持ち運びやすいタブレットです', 60000.00, 12, '電子機器', 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=300&fit=crop'),
('キーボード', '静音設計のメカニカルキーボードです', 12000.00, 30, '電子機器', 'https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400&h=300&fit=crop'),
('マウス', '高精度光学センサー搭載マウスです', 3000.00, 40, '電子機器', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=300&fit=crop'),
('モニター', '27インチ4Kディスプレイです', 45000.00, 6, '電子機器', 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=300&fit=crop'),
('ソファ', '快適なリビングソファです', 80000.00, 3, '家具', 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=300&fit=crop'),
('テーブル', 'シンプルなダイニングテーブルです', 25000.00, 7, '家具', 'https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=400&h=300&fit=crop'),
('ベッド', '快眠をサポートするベッドです', 120000.00, 4, '家具', 'https://images.unsplash.com/photo-1505693314120-0d443867891c?w=400&h=300&fit=crop'),
('ランプ', 'LED調光機能付きデスクランプです', 8000.00, 15, '家具', 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=300&fit=crop'),
('カメラ', '高画質デジタルカメラです', 35000.00, 8, '電子機器', 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400&h=300&fit=crop'),
('スピーカー', '高音質ワイヤレススピーカーです', 18000.00, 10, '電子機器', 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop'),
('腕時計', 'スマートウォッチです', 25000.00, 12, '雑貨', 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop'),
('財布', '本革製の高級財布です', 15000.00, 20, '雑貨', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop'),
('傘', '折りたたみ式の軽量傘です', 3000.00, 50, '雑貨', 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=300&fit=crop'),
('マグカップ', '保温性の高いマグカップです', 2000.00, 35, '雑貨', 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop'),
('ノート', '高品質の手帳です', 1500.00, 60, '雑貨', 'https://images.unsplash.com/photo-1531346680769-a1d79b57de5c?w=400&h=300&fit=crop'),
('ペン', '滑らかに書けるボールペンです', 500.00, 100, '雑貨', 'https://images.unsplash.com/photo-1583485088034-697b5bc36b35?w=400&h=300&fit=crop'),
('マスク', '使い捨てマスク100枚入りです', 1000.00, 80, '雑貨', 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=300&fit=crop'),
('ハンガー', 'プラスチック製のハンガーです', 800.00, 45, '雑貨', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop')
ON CONFLICT DO NOTHING;

-- サンプルレビュー (XSSテスト用)
INSERT INTO reviews (product_id, user_id, rating, comment) VALUES 
(1, 2, 5, 'とても良い商品です！'),
(2, 2, 4, '期待通りの品質でした'),
(3, 2, 3, '普通の商品です')
ON CONFLICT DO NOTHING;