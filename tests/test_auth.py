import os
import sys
import pytest
from flask import Flask, session
from flask_mail import Mail
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from campus_eats import UserTable, Customer, Restaurant
from auth.views import auth_blueprints, encrypt_password, get_session
from menus.views import menus_blueprints

@pytest.fixture
def app():
    app = Flask(__name__, template_folder='../templates')
    app.config['TESTING'] = True
    app.config['MAIL_SUPPRESS_SEND'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mysql@localhost/campus_eats' # 要記得改
    app.secret_key = os.urandom(24)
    app.register_blueprint(auth_blueprints)
    app.register_blueprint(menus_blueprints, url_prefix='/menus')
    mail = Mail(app)
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    Session = sessionmaker(bind=engine)
    with app.app_context():
        UserTable.metadata.create_all(engine)
        Customer.metadata.create_all(engine)
        Restaurant.metadata.create_all(engine)
    yield app
    engine.dispose()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def run_around_tests():
    # 清理數據庫
    with get_session() as db_session:
        db_session.query(Customer).delete()
        db_session.query(Restaurant).delete()
        db_session.query(UserTable).delete()
        db_session.commit()

def test_portal_login(client):
    response = client.get('/NCUlogin')
    assert response.status_code == 302
    assert response.location.startswith('https://portal.ncu.edu.tw/oauth2/authorization')

def test_callback_no_code(client):
    response = client.get('/customers/callback')
    assert response.status_code == 400
    assert b"Authorization code not found." in response.data

def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert "登入".encode('utf-8') in response.data

def test_register_get(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert "選擇角色註冊".encode('utf-8') in response.data

def test_logout(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location.endswith('/login')
    with client.session_transaction() as sess:
        assert 'username' not in sess

def test_forgot_password_get(client):
    response = client.get('/forgot_password')
    assert response.status_code == 200
    assert "忘記密碼".encode('utf-8') in response.data

def test_successful_login(client):
    with get_session() as db_session:
        user = UserTable(username='testuser', password=encrypt_password('testpassword'), role=1)
        customer = Customer(name='Customer Name', phone='1234567890', email='customer@example.com', username='testuser')
        db_session.add(user)
        db_session.add(customer)
        db_session.commit()

    response = client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
    assert response.status_code == 302, f"Expected status code 302, but got {response.status_code}"
    assert response.location.startswith('/menus/view_store'), f"Expected redirect to /menus/view_store, but got {response.location}"
    assert 'customer_id=' in response.location, f"Expected 'customer_id=' in the redirect URL, but got {response.location}"

    with client.session_transaction() as sess:
        assert sess.get('username') == 'testuser', f"Expected username 'testuser', but got {sess.get('username')}"
        assert sess.get('role') == 1, f"Expected role 1, but got {sess.get('role')}"
        assert 'customer_id' in sess, "Expected 'customer_id' in session"
        assert 'customer_name' in sess, "Expected 'customer_name' in session"

def test_failed_login(client):
    response = client.post('/login', data={'username': 'wronguser', 'password': 'wrongpassword'})
    assert response.status_code == 302
    assert "帳號或密碼錯誤！".encode('utf-8') in client.get(response.location).data

def test_successful_register_customer(client):
    response = client.post('/register', data={
        'role': 'customer',
        'username': 'newcustomer',
        'password': 'newpassword',
        'confirm_password': 'newpassword',
        'name': 'Customer Name',
        'phone': '1234567890',
        'email': 'customer@example.com'
    })
    assert response.status_code == 302
    assert response.location.endswith('/login')

def test_successful_register_restaurant(client):
    response = client.post('/register', data={
        'role': 'restaurant',
        'username': 'newrestaurant',
        'password': 'newpassword',
        'confirm_password': 'newpassword',
        'restaurant_name': 'Restaurant Name',
        'phone': '1234567890',
        'address': '123 Street',
        'manager': 'Manager Name',
        'manager_email': 'manager@example.com',
        'icon': (BytesIO(b'my file contents'), 'test.jpg')
    })
    assert response.status_code == 302
    assert response.location.endswith('/login')

def test_forgot_password_post(client):
    with get_session() as db_session:
        user = UserTable(username='testuser', password=encrypt_password('testpassword'), role=1)
        customer = Customer(name='Customer Name', phone='1234567890', email='customer@example.com', username='testuser')
        db_session.add(user)
        db_session.add(customer)
        db_session.commit()

    response = client.post('/forgot_password', data={'username': 'testuser', 'email': 'customer@example.com'})
    assert response.status_code == 302
    assert "新密碼已發送到您的電子郵件。".encode('utf-8') in client.get(response.location).data

def test_change_password_get(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    response = client.get('/change_password')
    assert response.status_code == 200
    assert "修改密碼".encode('utf-8') in response.data

def test_change_password_success(client):
    with get_session() as db_session:
        user = UserTable(username='testuser', password=encrypt_password('oldpassword'), role=1)
        db_session.add(user)
        db_session.commit()

    with client.session_transaction() as sess:
        sess['username'] = 'testuser'

    response = client.post('/change_password', data={
        'current_password': 'oldpassword',
        'new_password': 'newpassword',
        'confirm_password': 'newpassword'
    })
    assert response.status_code == 302
    assert response.location.endswith('/login')
    with get_session() as db_session:
        user = db_session.query(UserTable).filter_by(username='testuser').first()
        assert user.password == encrypt_password('newpassword')

def test_change_password_mismatch(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    response = client.post('/change_password', data={
        'current_password': 'oldpassword',
        'new_password': 'newpassword',
        'confirm_password': 'differentpassword'
    })
    assert response.status_code == 302
    assert "新密碼和確認密碼不一致".encode('utf-8') in client.get(response.location).data

def test_change_password_incorrect_current(client):
    with get_session() as db_session:
        user = UserTable(username='testuser', password=encrypt_password('oldpassword'), role=1)
        db_session.add(user)
        db_session.commit()

    with client.session_transaction() as sess:
        sess['username'] = 'testuser'

    response = client.post('/change_password', data={
        'current_password': 'wrongpassword',
        'new_password': 'newpassword',
        'confirm_password': 'newpassword'
    })
    assert response.status_code == 302
    assert "當前密碼不正確".encode('utf-8') in client.get(response.location).data

# To run the tests and generate an HTML report, use the following command:
# pytest --html=report.html