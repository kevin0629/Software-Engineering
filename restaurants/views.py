import os
from contextlib import contextmanager
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
from campus_eats import Restaurant, MenuItem, OrderTable, OrderDetail
# from menu_service import view_menu

# 建立實體
restaurants_blueprints = Blueprint('restaurants', __name__, template_folder='templates/restaurants', static_folder='./static')

# 創建資料庫引擎
# DATABASE_URL = 'mysql+pymysql://root:mysql@localhost/campus_eats'
DATABASE_URL = 'mysql+pymysql://root:@localhost/campus_eats' # Nicole
# DATABASE_URL = 'mysql+pymysql://root:113423027@mysql-1.cfg8ygkqmlab.ap-northeast-3.rds.amazonaws.com/campus_eats' # AWS

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



@restaurants_blueprints.route('management/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        # 從 session 取得資料
        restaurant_id = session.get('restaurant_id')

        item_name = request.form['item_name']
        price = request.form['price']
        description = request.form['description']
        status = request.form['status']
        item_image = request.files['item_image']

        with get_session() as db_session:
            item_exist = db_session.query(MenuItem).filter_by(item_name=item_name, restaurant_id=restaurant_id).first() is not None
            if item_exist:
                flash('餐點已存在')
                return redirect(url_for('restaurants.add_item'))

            if item_image and item_image.filename:
                last_item = db_session.query(MenuItem).order_by(desc(MenuItem.item_id)).first()
                item_id = None
                if last_item is None:
                    item_id = 0
                else:
                    item_id = last_item.item_id

                # 處理圖片
                filename, file_extension = os.path.splitext(item_image.filename)
                filename = str(item_id + 1) + file_extension
                image_path = os.path.join('images/menus', filename)  # 儲存相對路徑
                image_path = image_path.replace("\\", "/")  # 防止 Windows 路徑問題
                os.makedirs(os.path.dirname(os.path.join('./static', image_path)), exist_ok=True)  # 確保目錄存在
                item_image.save(os.path.join('./static', image_path))  # 儲存圖片
                
            else:
                image_path = 'images/menus/menu.png'  # 若無圖片則設為 None

            new_item = MenuItem(item_name=item_name, price=price, description=description, status=status, item_image=image_path,restaurant_id=restaurant_id)
            db_session.add(new_item)
            db_session.commit()

        return redirect(url_for('menus.view_menu', restaurant_id=restaurant_id))
    
    essential_data = {"restaurant_id": session.get('restaurant_id'), "restaurant_name": session.get('restaurant_name'), "icon": session.get('icon')}

    return render_template('restaurants/add_item.html', **essential_data)
    


@restaurants_blueprints.route('management/edit_store_info', methods=['GET', 'POST'])
def edit_store_info():
    if request.method == "POST":
        restaurant_id = session.get('restaurant_id')

        restaurant_name = request.form['restaurant_name']
        phone = request.form['phone']
        address = request.form['address']
        manager = request.form['manager']
        manager_email = request.form['manager_email']
        icon = request.files['icon']

        with get_session() as db_session:
            restaurant_info = db_session.query(Restaurant).filter_by(restaurant_id=restaurant_id).first()
            if icon and icon.filename:
                # 處理圖片
                filename, file_extension = os.path.splitext(icon.filename)
                filename = str(restaurant_info.restaurant_id) + file_extension
                image_path = os.path.join('images/restaurants', filename)  # 儲存相對路徑
                image_path = image_path.replace("\\", "/")
                os.makedirs(os.path.dirname(os.path.join('./static', image_path)), exist_ok=True)  # 確保目錄存在
                icon.save(os.path.join('./static', image_path))  # 儲存圖片
            else:
                image_path = restaurant_info.icon  # 若無圖片則設為之前的圖片

            restaurant_info.restaurant_name = restaurant_name
            restaurant_info.phone = phone
            restaurant_info.address = address

            hours = {}
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                times = request.form.getlist(f"{day}[]")
                hours[day] = [time for time in times if time]  # 過濾空值

            # 僅包含有時段的日子
            business_hours = ", ".join(f"{day}: {'、'.join(times)}" for day, times in hours.items() if times)
            restaurant_info.business_hours = business_hours
            restaurant_info.manager = manager
            restaurant_info.manager_email = manager_email
            restaurant_info.icon = image_path

            session['restaurant_name'] = restaurant_name
            session['icon'] = image_path

            db_session.commit()

        return redirect(url_for('menus.view_menu', restaurant_id=restaurant_id))

    return render_template('restaurants/profile.html')

@restaurants_blueprints.route('management/view_store_info')
def view_store_info():
    restaurant_id = session.get('restaurant_id')
    with get_session() as db_session:
        store_info = db_session.query(Restaurant).filter_by(restaurant_id=restaurant_id).first()

        # 初始化一個包含所有天的字典，值為空列表
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        business_hours = {day: [] for day in days_of_week}

        # 解析營業時間字串
        raw_business_hours = store_info.business_hours
        if raw_business_hours:
            # 分割每天的營業時間條目
            for entry in raw_business_hours.split(", "):
                day, times = entry.split(": ")
                # 將每一天的時段列表拆解後放入對應的 key
                business_hours[day] = times.split("、")

        store_data = {
                "restaurant_id": restaurant_id,
                "restaurant_name": store_info.restaurant_name,
                "phone": store_info.phone,
                "address": store_info.address,
                "business_hours": business_hours,
                "manager": store_info.manager,
                "manager_email": store_info.manager_email,
                "icon": store_info.icon
            }

    return render_template('restaurants/profile.html', **store_data)


@restaurants_blueprints.route('management/modify_item/<int:item_id>', methods=['GET', 'POST'])
def modify_item(item_id):
    if request.method == "POST":
        item_name = request.form['item_name']
        price = request.form['price']
        description = request.form['description']
        status = request.form['status']
        item_image = request.files['item_image']

        with get_session() as db_session:
            item_info = db_session.query(MenuItem).filter_by(item_id=item_id).first()

            if item_image and item_image.filename:
                # 處理圖片
                filename, file_extension = os.path.splitext(item_image.filename)
                filename = str(item_info.item_id) + file_extension
                image_path = os.path.join('images/menus', filename)  # 儲存相對路徑
                image_path = image_path.replace("\\", "/")  # 防止 Windows 路徑問題
                os.makedirs(os.path.dirname(os.path.join('./static', image_path)), exist_ok=True)  # 確保目錄存在
                item_image.save(os.path.join('./static', image_path))  # 儲存圖片
                
            else:
                image_path = item_info.item_image  # 若無圖片則設為上一張圖片

            item_info.item_name = item_name
            item_info.price = price
            item_info.description = description
            item_info.status = status

            db_session.commit()

            return redirect(url_for('menus.view_menu', restaurant_id=session.get('restaurant_id')))
        
@restaurants_blueprints.route('management/delete_item/<int:item_id>')
def delete_item(item_id):
    with get_session() as db_session:
        item_info = db_session.query(MenuItem).filter_by(item_id=item_id).first()

        db_session.delete(item_info)
        db_session.commit()

    return redirect(url_for('menus.view_menu', restaurant_id=session.get('restaurant_id')))

@restaurants_blueprints.route('management/view_order')
def view_order():
    restaurant_id = session.get('restaurant_id')

    with get_session() as db_session:
        # 查詢待處理訂單資料
        result = (
            db_session.query(
                OrderTable,
                OrderDetail.order_detail_id, OrderDetail.item_id, OrderDetail.item_note,
                OrderDetail.quantity, OrderDetail.item_price,
                MenuItem.item_name
            )
            .join(OrderTable, OrderDetail.order_id == OrderTable.order_id)
            .join(MenuItem, OrderDetail.item_id == MenuItem.item_id)
            .join(Restaurant, MenuItem.restaurant_id == Restaurant.restaurant_id)
            .filter(MenuItem.restaurant_id == restaurant_id, OrderTable.order_status.between(1,4), OrderTable.payment_status == 0)
            .order_by(desc(OrderTable.order_time))
            .all()
        )

        # 使用字典來分組資料
        order_process = {}
        for row in result:
            order_id = row[0].order_id
            total_amount = row[0].total_amount
            order_status = row[0].order_status
            order_time = row[0].order_time.strftime('%Y-%m-%d %H:%M:%S')
            payment_method = row[0].payment_method
            payment_status = row[0].payment_status
            order_note = row[0].order_note
            order_pick_up_time = row[0].order_pick_up_time.strftime('%Y-%m-%d %H:%M:%S')
            customer_id = row[0].customer_id
            order_detail_id = row[1]
            item_id = row[2]
            item_note = row[3]
            quantity = row[4]
            price = row[5]
            item_name = row[6]

            if not order_note:
                order_note = "無"
            
            if not item_note:
                item_note = "無"
            
            # 將訂單資訊加入字典中
            if order_id not in order_process:
                order_process[order_id] = {
                    "customer_id": customer_id,
                    "order_status": order_status,
                    "order_time": order_time,
                    "total_amount": total_amount,
                    "order_note": order_note,
                    "order_pick_up_time": order_pick_up_time,
                    "payment_status": "已付款" if payment_status == 1 else "未付款",
                    "payment_method": "現金" if payment_method == 1 else "信用卡" if payment_method == 2 else "尚未付款",

                    "order_details": {}
                }
                
            # 將訂單詳細資訊加入訂單
            if order_detail_id not in order_process[order_id]["order_details"]:
                order_process[order_id]["order_details"][order_detail_id] = {
                    "item_id": item_id,
                    "item_name": item_name,
                    "price": price,
                    "quantity": quantity,
                    "item_note": item_note
                }
    essential_data = {"restaurant_id": restaurant_id, "restaurant_name": session.get('restaurant_name'), "icon": session.get('icon'), "order_process": order_process}

    return render_template('restaurants/view_order.html', **essential_data)

@restaurants_blueprints.route('management/view_order/update_order_status', methods=['POST'])
def update_order_status():
    order_status = request.form['order_status']
    order_id = request.form['order_id']

    with get_session() as db_session:
        order_info = db_session.query(OrderTable).filter_by(order_id=order_id).first()
        order_info.order_status = order_status
        db_session.commit()

    return redirect(url_for('restaurants.view_order'))


@restaurants_blueprints.route('management/view_order/update_payment_status', methods=['POST'])
def update_payment_status():
    order_id = request.form['payment_order_id']
    payment_status = request.form['payment_status']

    with get_session() as db_session:
        order_info = db_session.query(OrderTable).filter_by(order_id=order_id).first()
        order_info.payment_status = payment_status
        db_session.commit()

    return redirect(url_for('restaurants.view_order'))

@restaurants_blueprints.route('management/view_history_order')
def view_history_order():
    restaurant_id = session.get('restaurant_id')

    with get_session() as db_session:
        # 查詢待處理訂單資料
        result = (
            db_session.query(
                OrderTable.order_id, OrderTable.total_amount, OrderTable.order_time, OrderTable.payment_method,
                OrderTable.order_note, OrderTable.order_pick_up_time, OrderTable.customer_id,
                OrderDetail.order_detail_id, OrderDetail.item_id, OrderDetail.item_note,
                OrderDetail.quantity, OrderDetail.item_price,
                MenuItem.item_name
            )
            .join(OrderTable, OrderDetail.order_id == OrderTable.order_id)
            .join(MenuItem, OrderDetail.item_id == MenuItem.item_id)
            .join(Restaurant, MenuItem.restaurant_id == Restaurant.restaurant_id)
            .filter(MenuItem.restaurant_id == restaurant_id, OrderTable.payment_status == 1)
            .order_by(desc(OrderTable.order_time))
            .all()
        )


        # 使用字典來分組資料
        history_order = {}
        for row in result:
            order_id = row[0]
            total_amount = row[1]
            order_time = row[2].strftime('%Y-%m-%d %H:%M:%S')
            payment_method = row[3]
            order_note = row[4]
            order_pick_up_time = row[5].strftime('%Y-%m-%d %H:%M:%S')  # 將 datetime 轉換為字符串
            customer_id = row[6]
            order_detail_id = row[7]
            item_id = row[8]
            item_note = row[9]
            quantity = row[10]
            price = row[11]
            item_name = row[12]

            if not order_note:
                order_note = "無"
            
            if not item_note:
                item_note = "無"
            
            # 將訂單資訊加入字典中
            if order_id not in history_order:
                history_order[order_id] = {
                    "customer_id": customer_id,
                    "order_time": order_time,
                    "total_amount": total_amount,
                    "order_note": order_note,
                    "order_pick_up_time": order_pick_up_time,
                    "payment_method": "現金" if payment_method == 1 else "信用卡" if payment_method == 2 else "尚未付款",

                    "order_details": {}
                }
                
            # 將訂單詳細資訊加入訂單
            if order_detail_id not in history_order[order_id]["order_details"]:
                history_order[order_id]["order_details"][order_detail_id] = {
                    "item_id": item_id,
                    "item_name": item_name,
                    "price": price,
                    "quantity": quantity,
                    "item_note": item_note
                }

    essential_data = {"restaurant_id": restaurant_id, 
                      "restaurant_name": session.get('restaurant_name'), 
                      "icon": session.get('icon'), 
                      "history_order": history_order, 
                      }

    return render_template('restaurants/view_history_order.html', **essential_data)