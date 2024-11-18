import os
from flask import Flask, render_template
from customers.views import customers_blueprints
from restaurants.views import restaurants_blueprints
from auth.views import auth_blueprints
import campus_eats

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24) 

app.register_blueprint(customers_blueprints, url_prefix='/customers')
app.register_blueprint(restaurants_blueprints, url_prefix='/restaurants')
app.register_blueprint(auth_blueprints)

# 登入頁面
@app.route('/')
def home():
    return render_template('auth/login.html')

# 訪客/店家頁面
@app.route('/register')
def register():
    return 0

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug=True) #aws
    app.run(debug=True)


