import os
import requests
from flask import Blueprint, redirect, request

# 建立實體
customers_blueprints = Blueprint( 'customers', __name__, template_folder= 'templates/customers', static_folder='./static')

customers_blueprints.secret_key = os.urandom(24)  # Session 加密用
# OAuth 設定
CLIENT_ID = '20241007203637hgWIOoOg6QGH'  # 從中央大學 Portal 申請
CLIENT_SECRET = 'YUustASvU0LWPSFXygagued9EILygcfv4h3xofCYJYAuQEoMXrLatvFy'  # 從中央大學 Portal 申請
AUTHORIZATION_URL = 'https://portal.ncu.edu.tw/oauth2/authorization'
TOKEN_URL = 'https://portal.ncu.edu.tw/oauth2/token'
USER_INFO_URL = 'https://portal.ncu.edu.tw/apis/oauth/v1/info'
REDIRECT_URI = 'http://localhost:5000/customers/callback'  # 回調 URL
SCOPE = 'id identifier chinese-name email mobile-phone'


@customers_blueprints.route('/NCUlogin', methods=['GET','POST'])
def portal():
    return redirect(f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}')

# 授權完成後的回調處理
@customers_blueprints.route('/callback')
def callback():
    # 取得授權碼
    code = request.args.get('code')

    if not code:
        return "Authorization code not found.", 400

    # 交換授權碼為 access token
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }, headers={
        'Accept': 'application/json'
    })

    # 確認 token 回應
    token_json = token_response.json()
    if 'access_token' not in token_json:
        return "Failed to get access token.", 400

    access_token = token_json['access_token']

    # 使用 access token 取得使用者資訊
    user_info_response = requests.get(USER_INFO_URL, headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    })

    user_info = user_info_response.json()
    print(user_info)

    # 將抓取到的資料寫進資料庫

    # call back (return) 餐廳 list

    # 顯示使用者資訊 (要改掉)
    return f'''
        <h1>User Info</h1>
        <p>ID: {user_info.get('id')}</p>
        <p>Identifier: {user_info.get('identifier')}</p>
        <p>Chinese Name: {user_info.get('chineseName')}</p>
        <p>Email: {user_info.get('email')}</p>
        <p>Phone: {user_info.get('mobilePhone')}</p>
    '''
