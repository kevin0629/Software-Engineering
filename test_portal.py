import os
import requests
from flask import Flask, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Session 加密用

# OAuth 設定
CLIENT_ID = '20241007203637hgWIOoOg6QGH'  # 從中央大學 Portal 申請
CLIENT_SECRET = 'YUustASvU0LWPSFXygagued9EILygcfv4h3xofCYJYAuQEoMXrLatvFy'  # 從中央大學 Portal 申請
AUTHORIZATION_URL = 'https://portal.ncu.edu.tw/oauth2/authorization'
TOKEN_URL = 'https://portal.ncu.edu.tw/oauth2/token'
USER_INFO_URL = 'https://portal.ncu.edu.tw/apis/oauth/v1/info'
REDIRECT_URI = 'http://localhost:5000/callback'  # 回調 URL
SCOPE = 'id identifier chinese-name email mobile-phone'

# 登入頁面
@app.route('/')
def login():
    return '''
        <h1>Welcome to OAuth2 SSO Login</h1>
        <a href="/login">Login with NCU OAuth2</a>
    '''

# 授權步驟：重導向到中央大學 OAuth 授權頁面
@app.route('/login')
def login_redirect():
    return redirect(f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}')

# 授權完成後的回調處理
@app.route('/callback')
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

    # 顯示使用者資訊
    return f'''
        <h1>User Info</h1>
        <p>ID: {user_info.get('id')}</p>
        <p>Identifier: {user_info.get('identifier')}</p>
        <p>Chinese Name: {user_info.get('chineseName')}</p>
        <p>Email: {user_info.get('email')}</p>
        <p>Phone: {user_info.get('mobilePhone')}</p>
    '''

if __name__ == '__main__':
    app.run(debug=True)