-- 用戶資料表
CREATE TABLE user_table (
    username VARCHAR(50) PRIMARY KEY COMMENT '用戶帳號，PK',
    password VARCHAR(255) NOT NULL COMMENT '用戶密碼',
    role INT NOT NULL COMMENT '用戶角色（1顧客、2店家）'
) COMMENT '用戶基本資訊表';

-- 顧客資料表
CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '顧客ID，自動遞增，PK',
    name VARCHAR(100) NOT NULL COMMENT '顧客姓名',
    phone VARCHAR(20) COMMENT '顧客電話號碼',
    email VARCHAR(100) COMMENT '顧客電子郵件',
    username VARCHAR(50) COMMENT '對應用戶帳號（FK）',
    FOREIGN KEY (username) REFERENCES user_table(username)
) COMMENT '顧客詳細資料表';

-- 店家資料表
CREATE TABLE restaurant (
    restaurant_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '店家ID，自動遞增，PK',
    restaurant_name VARCHAR(100) NOT NULL COMMENT '店家名稱',
    phone VARCHAR(20) COMMENT '店家電話號碼',
    address VARCHAR(255) COMMENT '店家地址',
    business_hours VARCHAR(100) COMMENT '店家營業時間',
    manager VARCHAR(50) COMMENT '店家負責人',
    icon VARCHAR(255) COMMENT '店家圖示（URL）',
    username VARCHAR(50) COMMENT '對應用戶帳號（FK）',
    FOREIGN KEY (username) REFERENCES user_table(username)
) COMMENT '店家資料表';

-- 餐點資料表
CREATE TABLE menu_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '餐點ID，自動遞增，PK',
    item_name VARCHAR(100) NOT NULL COMMENT '餐點名稱',
    price DECIMAL(10, 2) NOT NULL COMMENT '餐點價格',
    description TEXT COMMENT '餐點描述',
    status INT COMMENT '餐點狀態（0停售、1販售中）',
    item_image VARCHAR(255) COMMENT '餐點圖片URL',
    restaurant_id INT COMMENT '所屬店家ID（FK）',
    FOREIGN KEY (restaurant_id) REFERENCES restaurant(restaurant_id)
) COMMENT '餐點資料表，記錄每個店家的餐點';

-- 訂單資料表
CREATE TABLE order_table (
    order_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單ID，自動遞增，PK',
    total_amount DECIMAL(10, 2) NOT NULL COMMENT '訂單總金額',
    order_status INT NOT NULL COMMENT '訂單狀態（如：0下單前(在購物車中)、1待處理、2店家確認、3處理中、4已完成、5已刪除）',
    order_time DATETIME NOT NULL COMMENT '訂單建立時間',
    payment_method INT COMMENT '付款方式（如：1現金、2信用卡）',
    payment_status INT COMMENT '付款狀態（如：0未付款、1已付款）',
    order_note TEXT COMMENT '訂單備註',
    customer_id INT COMMENT '對應的顧客ID（FK）',
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
) COMMENT '訂單資料表，記錄每筆訂單的基本資訊';

-- 訂單明細表
CREATE TABLE order_detail (
    order_detail_id INT AUTO_INCREMENT COMMENT '訂單明細ID，自動遞增，複合主鍵',
    order_id INT COMMENT '對應的訂單ID（複合主鍵、FK）',
    item_id INT COMMENT '對應的餐點ID（FK）',
    item_note TEXT COMMENT '餐點備註',
    quantity INT NOT NULL COMMENT '購買的餐點數量',
    PRIMARY KEY (order_detail_id, order_id),
    FOREIGN KEY (order_id) REFERENCES order_table(order_id),
    FOREIGN KEY (item_id) REFERENCES menu_item(item_id)
) COMMENT '訂單明細表，記錄每筆訂單的餐點詳情';
