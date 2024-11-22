import os
from contextlib import contextmanager
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from campus_eats import Restaurant, MenuItem
from menu_service import view_menu

# 建立實體
restaurants_blueprints = Blueprint('restaurants', __name__, template_folder='templates/restaurants', static_folder='./static')

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




# @restaurants_blueprints.route('/management')
# def management():
#     # 返回菜單頁面
#     if session.get('role') != 2:
#         return redirect(url_for('auth.login'))

#     restaurant_id = session.get('restaurant_id')
#     menu_info = view_menu(restaurant_id)

#     with get_session() as db_session:
#         restaurant_info = db_session.query(Restaurant).filter_by(restaurant_id=restaurant_id).first()
#         data = {
#             "restaurant_name": restaurant_info.restaurant_name,
#             "phone": restaurant_info.phone,
#             "address": restaurant_info.address,
#             "business_hours": restaurant_info.business_hours,
#             "manager": restaurant_info.manager,
#             "icon": restaurant_info.icon,
#             "menu_items": menu_info
#         }

#     return render_template('restaurants/management.html', **data)



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
                last_item = db_session.query(MenuItem).filter_by(restaurant_id=restaurant_id).order_by(desc(MenuItem.item_id)).first()
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