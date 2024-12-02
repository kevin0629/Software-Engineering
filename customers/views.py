import os
from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from contextlib import contextmanager
from campus_eats import UserTable, Customer , OrderTable, OrderDetail
from datetime import datetime

# 建立實體
customers_blueprints = Blueprint('customers', __name__, template_folder='templates/customers', static_folder='./static')

# 創建資料庫引擎
# DATABASE_URL = 'mysql+pymysql://root:mysql@localhost/campus_eats'
DATABASE_URL = 'mysql+pymysql://root:@localhost/campus_eats' # Nicole
# DATABASE_URL = 'mysql+pymysql://root:113423027@13.208.142.64/campus_eats' # AWS

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# 創建一個上下文管理器來自動管理 Session 的生命週期
@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()  # 若有任何變更需要提交
    except Exception as e:
        session.rollback()  # 發生錯誤時回滾事務
        raise
    finally:
        session.close()  # 結束後關閉 session

@customers_blueprints.route('/menu')
def menu():
    # 返回菜單頁面
    return render_template('customers/view_store.html')

@customers_blueprints.route('/add_to_cart', methods=['GET', 'POST']) 
def add_to_cart():  # 新增餐點進購物車
    if request.method == 'POST':
        item_id = request.form['item_id']  # 現在要購買之餐點 id
        redirect_flag = int(request.form.get('redirect_flag'))
        restaurant_id = get_restaurant_id_for_item(item_id) # 目前購買餐點的所屬餐廳
        customer_id = session.get('customer_id')  # 目前使用者 id
        all_active_orders = check_existing_orders(customer_id) # 目前有的購物車
    
        # 檢查是否已存在相同餐廳的訂單
        existing_order = None
        for order in all_active_orders: # 如果有抓取現有的
            if order['restaurant_id'] == restaurant_id:
                existing_order = order['order_id']
                break

        if not existing_order: # 如果無則建立新的訂單
            existing_order = checkOrder(customer_id)
            
        add_one_item_in_Cart(item_id, existing_order)
        if redirect_flag == 1:
            return redirect(url_for('customers.view_cart'))
            
        else:
            return redirect(url_for('menus.view_menu', restaurant_id=restaurant_id))

def add_one_item_in_Cart(item_id, order_id):  # 新增一份餐點進入購物車
    with get_session() as db_session:
        existing_order_detail = db_session.query(OrderDetail).filter_by(  # 確認目前是否有同筆商品的訂單細項
                order_id=order_id,
                item_id=item_id
            ).first()
        if existing_order_detail:  # 如果有則直接將數量加一
            existing_order_detail.quantity += 1
            db_session.commit()  # 提交變更
        else:
            new_order_detail = OrderDetail(
                order_id=order_id,
                item_id=item_id,
                quantity=1  # 新增時初始數量為 1
            )
            db_session.add(new_order_detail)
            db_session.commit()  # 提交新記錄

def checkOrder(customer_id):  # 新增一筆新的訂單
    with get_session() as db_session:
        current_time = datetime.now()  # 記錄下訂單的時間
        new_order = OrderTable(
            order_status=0,
            total_amount=0,
            payment_status=0,
            customer_id=customer_id,
            order_time=current_time
        )
        db_session.add(new_order)
        db_session.commit()

        # 獲取新建訂單的 ID
        db_session.refresh(new_order)  # 刷新以獲取新插入的 id
        return new_order.order_id if new_order else None

def get_restaurant_id_for_item(item_id): # 查詢該產品所屬的店家
    with get_session() as db_session:
        query = text("""
            SELECT restaurant_id
            FROM menu_item
            WHERE item_id = :item_id;
            """)
        result = db_session.execute(query, {"item_id": item_id}).scalar()
        return result if result else None
    
def check_existing_orders(customer_id): # 查當前用戶擁有的所有購物車
    # 查找所有屬於該使用者且狀態為零的訂單
    with get_session() as db_session:
        query = text("""
            SELECT order_id
            FROM order_table
            WHERE customer_id = :customer_id AND order_status = 0;
            """)
        orders = db_session.execute(query, {"customer_id": customer_id}).fetchall()
    
    # 根據訂單的 id 去訂單細項表格隨便抓取一格內容商品，並在通過該商品之編號去menu表格裡查詢所屬店家
    restaurant_ids = []
    for order in orders:
        order_id = order[0]
        # 從訂單細項表中隨便抓取一筆內容商品
        with get_session() as db_session:
            item_query = text("""
                SELECT item_id
                FROM order_detail
                WHERE order_id = :order_id
                LIMIT 1;
                """)
            item_id = db_session.execute(item_query, {"order_id": order_id}).scalar()
        
        if item_id:
            # 通過該商品的編號去 menu_item 表格查詢所屬店家
            restaurant_id = get_restaurant_id_for_item(item_id)
            if restaurant_id:
                restaurant_ids.append({"order_id": order_id, "restaurant_id": restaurant_id})

    return restaurant_ids

@customers_blueprints.route('/view_cart')
def view_cart(): # 查看購物車內容
    customer_id = session.get('customer_id')  # 目前使用者 id
    customer_name = session.get('customer_name')
    order_list = fetch_cart_item(customer_id) # 目前所有購物車資料
    return render_template('customers/view_cart.html',cart_items = order_list,customer_name = customer_name)

def fetch_cart_item(customer_id):  # 抓取目前所擁有的所有購物車
    with get_session() as session:
        query = text("""
            SELECT order_table.order_id, order_table.order_note, order_detail.order_detail_id, order_detail.item_id, 
                   menu_item.item_name, menu_item.price, order_detail.quantity, order_detail.item_note, 
                   menu_item.restaurant_id, restaurant.restaurant_name
            FROM order_table
            JOIN order_detail ON order_table.order_id = order_detail.order_id
            JOIN menu_item ON order_detail.item_id = menu_item.item_id
            JOIN restaurant ON restaurant.restaurant_id = menu_item.restaurant_id
            WHERE order_table.order_status = 0 AND order_table.customer_id = :customer_id;
        """)
        result = session.execute(query, {"customer_id": customer_id}).fetchall()
        
        # 使用字典來分組資料
        grouped_cart_items = {}
        for row in result:
            order_id = row[0]
            order_note = row[1]
            order_detail_id = row[2]
            item_id = row[3]
            item_name = row[4]
            item_price = row[5]
            item_quantity = row[6]
            item_note = row[7]
            restaurant_id = row[8]
            restaurant_name = row[9]

            # 計算單筆商品的小計
            item_total_price = item_price * item_quantity
            
            # 如果這個餐廳還沒有被添加到字典中
            if restaurant_id not in grouped_cart_items:
                grouped_cart_items[restaurant_id] = {
                    "restaurant_name": restaurant_name,
                    "order_id": order_id,  # 新增 order_id 到與 restaurant_id 同一層
                    "order_note": order_note,  # 新增整筆訂單的備註
                    "items": [],
                    "total_price": 0
                }
            
            # 將商品資訊添加到對應餐廳的 items 列表中
            grouped_cart_items[restaurant_id]["items"].append({
                "order_detail_id": order_detail_id,
                "order_id": order_id,
                "item_id": item_id,
                "item_name": item_name,
                "price": item_price,
                "quantity": item_quantity,
                "item_note": item_note,  # 為每個商品新增細項備註
                "item_total_price": item_total_price  # 計算單筆商品的小計
            })

            # 增加餐廳的總金額
            grouped_cart_items[restaurant_id]["total_price"] += item_total_price

        print(grouped_cart_items)
    return grouped_cart_items

@customers_blueprints.route('/remove_from_cart', methods=['POST'])
def remove_from_cart(): # 移除一個商品
    if request.method == 'POST':   
        order_id = request.form['order_id']
        order_detail_id = request.form['order_detail_id']

        # 檢查是否有相應的訂單
        with get_session() as db_session:
            existing_order_detail = db_session.query(OrderDetail).filter_by(
                order_detail_id=order_detail_id,
                order_id = order_id
            ).first()

            if existing_order_detail:
                if existing_order_detail.quantity > 1:
                    # 如果數量大於 1，則減少一個
                    existing_order_detail.quantity -= 1
                    db_session.commit()  
                else:
                    # 如果數量為 1，則刪除該項目
                    db_session.delete(existing_order_detail)
                    db_session.commit()  
                    update_order_status_if_empty(db_session, order_id)
 
    return redirect(url_for('customers.view_cart'))

def update_order_status_if_empty(db_session, order_id): # 檢查該訂單是否還有其他訂單細項
    with get_session() as db_session:
        remaining_items = db_session.query(OrderDetail).filter_by(
            order_id=order_id,
        ).count()

    if remaining_items == 0:
        # 如果沒有其他餐點，將訂單狀態改為 5 (已取消)
        existing_order = db_session.query(OrderTable).filter_by(order_id=order_id).first()
        if existing_order:
            existing_order.order_status = 5
            db_session.commit() 

@customers_blueprints.route('/checkout_order', methods=['POST'])
def checkout_order():  # 送出訂單
    if request.method == 'POST':
        order_id = request.form['order_id']
        total_price = request.form['total_price']
        payment_method = request.form['payment_method']  # 新增獲取付款方式

        # 更新訂單狀態、總金額和付款方式
        with get_session() as db_session:
            order = db_session.query(OrderTable).filter_by(order_id=order_id).first()

            if order:
                order.order_status = 1  # 設定狀態為 1 表示已送出
                order.total_amount = total_price  # 更新總金額
                order.payment_method = payment_method  # 更新付款方式

                db_session.commit() 

        return redirect(url_for('customers.view_cart')) 

@customers_blueprints.route('/view_order')
def view_order(): # 查看歷史已送出之訂單
    customer_name = session.get('customer_name')
    customer_id = session.get('customer_id')
    order_all_list = fetch_all_orders(customer_id)
    return render_template('customers/view_order.html',customer_name=customer_name, order_all_list= order_all_list)

def fetch_all_orders(customer_id):  # 抓取所有狀態非 0 和 5 的屬於指定客戶的訂單
    with get_session() as session:
        query = text("""
            SELECT order_table.order_id, order_table.customer_id, order_table.order_status, order_table.order_time, order_table.total_amount,
                   order_table.payment_status, order_table.payment_method,
                   order_detail.order_detail_id, order_detail.item_id, menu_item.item_name, menu_item.price, order_detail.quantity,
                   menu_item.restaurant_id, restaurant.restaurant_name
            FROM order_table
            JOIN order_detail ON order_table.order_id = order_detail.order_id
            JOIN menu_item ON order_detail.item_id = menu_item.item_id
            JOIN restaurant ON restaurant.restaurant_id = menu_item.restaurant_id
            WHERE order_table.order_status NOT IN (0, 5) AND order_table.customer_id = :customer_id;
        """)
        result = session.execute(query, {"customer_id": customer_id}).fetchall()
        
        # 使用字典來分組資料
        grouped_orders = {}
        for row in result:
            order_id = row[0]
            customer_id = row[1]
            order_status = row[2]
            order_time = row[3]
            total_amount = row[4]
            payment_status = row[5]
            payment_method = row[6]
            restaurant_id = row[12]
            restaurant_name = row[13]
            
            # 將訂單資訊加入字典中
            if order_id not in grouped_orders:
                grouped_orders[order_id] = {
                    "customer_id": customer_id,
                    "order_status": order_status,
                    "order_time": order_time,
                    "total_amount": total_amount,
                    "payment_status": "已付款" if payment_status == 1 else "未付款",
                    "payment_method": "現金" if payment_method == 1 else "信用卡" if payment_method == 2 else "尚未付款",

                    "restaurants": {}
                }
                
            # 將餐廳資訊加入訂單
            if restaurant_id not in grouped_orders[order_id]["restaurants"]:
                grouped_orders[order_id]["restaurants"][restaurant_id] = {
                    "restaurant_name": restaurant_name,
                    "items": []
                }
                
            # 將餐點資訊加入餐廳
            grouped_orders[order_id]["restaurants"][restaurant_id]["items"].append({
                "order_detail_id": row[7],
                "item_id": row[8],
                "item_name": row[9],
                "price": row[10],
                "quantity": row[11]
            })

        print("歷史訂單：", grouped_orders)
    return grouped_orders

@customers_blueprints.route('/return_order', methods=['POST'])
def return_order(): # 修改訂單狀態回到退回
    order_id = request.form['order_id']
    
    if not order_id:
        flash('無效的訂單 ID', 'error')
        return redirect(url_for('customers.view_order'))

    with get_session() as db_session:
        # 更新訂單狀態並清零總金額
        order = db_session.query(OrderTable).filter_by(order_id=order_id).first()
        if order:
            order.order_status = 0  # 訂單狀態設置為 "尚未送出"
            order.total_amount = 0  # 清零總金額
            db_session.commit()  # 提交變更
            flash('訂單狀態已退回尚未送出，且總金額已清零。請至購物車頁面進行修改！', 'success')
        else:
            flash('未找到該訂單，請檢查後再試。', 'error')

    return redirect(url_for('customers.view_order'))

@customers_blueprints.route('/view_pf')
def view_pf(): # 抓取原始的個人資料
    customer_id = session.get('customer_id')
    customer_name = session.get('customer_name')
   
    with get_session() as db_session:
        # 先從資料庫中抓取目前使用者的資料
        data = db_session.query(Customer).filter_by(customer_id=customer_id).first()

        if not data:
            flash("找不到您的資料，請重新登錄", "error")
            return redirect(url_for('auth.login'))

        # 將資料轉換成字典
        customer_data = {
            "name": data.name,
            "phone": data.phone,
            "email": data.email
        }

    return render_template('customers/view_customer_pf.html', customer_name=customer_name, customer_pf=customer_data)

@customers_blueprints.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile(): # 獲取當前客戶信息
    customer_id = session.get('customer_id')
    
    if request.method == 'POST': # 獲取表單中的輸入數據
        new_name = request.form.get('name')
        new_phone = request.form.get('phone')
        new_email = request.form.get('email')

        with get_session() as db_session:
            # 查找當前客戶的數據
            customer = db_session.query(Customer).filter_by(customer_id=customer_id).first()

            if not customer:
                flash("無法找到您的個人資料，請重新登錄。", "error")
                return redirect(url_for('auth.login'))

            # 檢查數據是否變更，並進行更新
            if customer.name != new_name:
                customer.name = new_name
            if customer.phone != new_phone:
                customer.phone = new_phone
            if customer.email != new_email:
                customer.email = new_email

            # 提交修改到資料庫
            db_session.commit()
            flash("您的個人資料已成功更新！", "success")

    # 重定向回顯示個人資料的頁面
    return redirect(url_for('customers.view_pf'))

@customers_blueprints.route('/add_note', methods=['POST'])
def add_note(): # 新增備註
    customer_id = session.get('customer_id') 
    order_id = request.form.get('order_id') 
    order_detail_id = request.form.get('order_detail_id')
    note_text = request.form.get('note')

    if not note_text:
        flash("請輸入備註內容", "error")
        return redirect(url_for('customers.view_cart'))

    with get_session() as db_session:
        if order_detail_id:
            # 如果有 order_detail_id，則是給餐點新增備註
            order_detail = db_session.query(OrderDetail).filter_by(order_detail_id=order_detail_id, order_id=order_id).first()
            if order_detail:
                order_detail.item_note = note_text
            else:
                flash("找不到訂單細項，請重試", "error")
                return redirect(url_for('customers.view_cart'))
        else:
            # 沒有 order_detail_id，則是給整筆訂單新增備註
            order = db_session.query(OrderTable).filter_by(order_id=order_id, customer_id=customer_id).first()
            if order:
                order.order_note = note_text
            else:
                flash("找不到訂單，請重試", "error")
                return redirect(url_for('customers.view_cart'))

        # 提交修改到資料庫
        db_session.commit()
        flash("備註新增成功！", "success")

    return redirect(url_for('customers.view_cart'))
