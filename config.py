import os

class Config:
    # 'DATABASE_URL' 是環境變數的名稱
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://auebtznvfn:Se113423000@ncucampuseats-server.mysql.database.azure.com/campus_eats')


    # SQLALCHEMY_TRACK_MODIFICATIONS 是 SQLAlchemy 中的一個設定選項，它的作用與資料庫連線的事件監控有關。
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # test cicd
