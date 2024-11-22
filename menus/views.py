import os
from contextlib import contextmanager
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from campus_eats import Restaurant, MenuItem
from datetime import datetime, timezone, timedelta


menus_blueprints = Blueprint('menus', __name__, static_folder='./static')

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



@menus_blueprints.route('/view_store')
def view_store():
    if not session.get('role'):
        return redirect(url_for('auth.login'))

    with get_session() as db_session:
        store_info = db_session.query(Restaurant).all()

        # 定義台灣時區
        taiwan_tz = timezone(timedelta(hours=+8))

        # 取得當前台灣的日期和時間
        now = datetime.now(taiwan_tz)
        current_day = now.strftime("%A")  # 當前星期
        current_time = now.time()  # 當前時間

        print("current_time: ", current_time)

        valid_stores = []

        for store in store_info:
            raw_business_hours = store.business_hours
            if not raw_business_hours:
                continue  # 無營業時間資料的店家跳過

            # 找出當天的營業時間
            try:
                today_hours = next(
                    (times for day, times in (entry.split(": ") for entry in raw_business_hours.split(", ")) if day == current_day),
                    None
                )
                if not today_hours:
                    continue  # 如果當天無營業時間則跳過
            except ValueError:
                continue  # 格式錯誤的營業時間跳過

            # 分割時間區間並檢查是否符合當前時間
            is_open = any(
                start <= current_time <= end
                for start, end in (
                    map(lambda t: datetime.strptime(t.strip(), "%H:%M").time(), time_range.split("~"))
                    for time_range in today_hours.split("、")
                )
            )
            if is_open:
                valid_stores.append({
                    "restaurant_id": store.restaurant_id,
                    "restaurant_name": store.restaurant_name,
                    "phone": store.phone,
                    "address": store.address,
                    "business_hours": store.business_hours,
                    "icon": store.icon
                })

        # 將營業中的店家資料傳遞到模板
        data = {"username": session.get('username'), "openedRestaurants": valid_stores}

    return render_template('customers/view_store.html', **data)
    


@menus_blueprints.route('/view_menu/<int:restaurant_id>')
def view_menu(restaurant_id):
    role = session.get('role')
    if not role:
        return redirect(url_for('auth.login'))
    
    with get_session() as db_session:
        menu_info = db_session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
        restaurant_info = db_session.query(Restaurant).filter_by(restaurant_id=restaurant_id).first()
        
        restaurant_data = {
            "restaurant_name": restaurant_info.restaurant_name,
            "phone": restaurant_info.phone,
            "address": restaurant_info.address,
            "business_hours": restaurant_info.business_hours,
            "icon": restaurant_info.icon
        }
        # 將 MenuItem 的資料提取為字典
        menu_items = [
            {
                "item_id": item.item_id,
                "item_name": item.item_name,
                "price": item.price,
                "description": item.description,
                "status": item.status,
                "item_image": item.item_image
            }
            for item in menu_info
        ]

    if role == 1:
        data = {
            "username": session.get('username'),
            "restaurant": restaurant_data,
            "menu_items": menu_items  # 使用轉換過的資料
        }
        return render_template('customers/view_menu.html', **data)
    else:
        # 包裝資料以傳遞給模板
        data = {
            "restaurant_id": restaurant_id,
            "restaurant_name": session.get('restaurant_name'),
            "icon": session.get('icon'),
            "menu_items": menu_items  # 使用轉換過的資料
        }
        return render_template('restaurants/management.html', **data)


@menus_blueprints.route('/view_detailed_menu/<int:item_id>')
def view_detailed_menu(item_id):
    with get_session() as db_session:
        menu_info = db_session.query(MenuItem).filter_by(item_id=item_id).first()

        data = {
                "restaurant_id": session.get('restaurant_id'),
                "restaurant_name": session.get('restaurant_name'),
                "icon": session.get('icon'),
                "item_id": menu_info.item_id,
                "item_name": menu_info.item_name,
                "price": menu_info.price,
                "description": menu_info.description,
                "status": menu_info.status,
                "item_image": menu_info.item_image
            }

    return render_template('restaurants/modify_item.html', **data)