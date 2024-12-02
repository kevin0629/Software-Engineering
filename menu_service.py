import os
from contextlib import contextmanager
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from campus_eats import Restaurant, MenuItem


menus_blueprints = Blueprint('menus', __name__, static_folder='./static')

menus_blueprints.secret_key = os.urandom(24)  # Session 加密用

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


def view_store():
    with get_session() as db_session:
        store_info = db_session.query(Restaurant).all()

    return store_info
    

def view_menu(restaurant_id):
    with get_session() as db_session:
        menu_info = db_session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()

        menu_data = [
            {
                "item_name": item.item_name,
                "price": int(item.price),
                "description": item.description,
                "status": item.status,
                "item_image": item.item_image
            }
            for item in menu_info
        ]

    return menu_data