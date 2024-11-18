import os
from contextlib import contextmanager
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from campus_eats import Restaurant, UserTable, MenuItem

# 建立實體
restaurants_blueprints = Blueprint('restaurants', __name__, template_folder='templates/restaurants', static_folder='./static')

restaurants_blueprints.secret_key = os.urandom(24)  # Session 加密用

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




@restaurants_blueprints.route('/management')
def management():
    # 返回菜單頁面
    if 'username' not in session or session.get('role') != 2:
        return redirect(url_for('auth.login'))

    # 從 session 取得資料
    restaurant_name = session.get('restaurant_name')
    phone = session.get('phone')
    address = session.get('address')
    business_hour = session.get('business_hour')
    manager = session.get('manager')
    icon = session.get('icon')

    return render_template('restaurants/management.html', 
                           restaurant_name=restaurant_name, 
                           phone=phone, 
                           address=address, 
                           business_hour=business_hour,
                           manager=manager,
                           icon=icon)

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
            # 查詢某餐廳的最後一個菜單項目（根據 id 排序，取最大 id 的項目）
            if item_image:
                last_item = db_session.query(MenuItem).filter_by(restaurant_id=restaurant_id).order_by(desc(MenuItem.item_id)).first()
                item_id = None
                if last_item is None:
                    item_id = 0
                else:
                    item_id = last_item.item_id
                # 處理圖片
                if item_image.filename:
                    filename, file_extension = os.path.splitext(item_image.filename)
                    filename = str(item_id + 1) + file_extension
                    image_path = os.path.join('./static/images/menus', filename)
                    image_path = image_path.replace("\\", "/")
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)  # 確保目錄存在
                    item_image.save(image_path)
                else:
                    image_path = None  # 若無圖片則設為 None

            is_user_exist = db_session.query(MenuItem).filter_by(item_name=item_name, restaurant_id=restaurant_id).first() is not None
            if is_user_exist:
                flash('餐點已存在')
                return redirect(url_for('restaurants.add_item'))

            new_item = MenuItem(item_name=item_name, price=price, description=description, status=status, item_image=image_path,restaurant_id=restaurant_id)
            db_session.add(new_item)
            db_session.commit()
            print('餐點新增成功！')

        return redirect(url_for('restaurants.management'))
    

@restaurants_blueprints.route('management/edit_store_info', methods=['GET', 'POST'])
def edit_store_info():
    return True