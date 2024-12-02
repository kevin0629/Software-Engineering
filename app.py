import os
from flask import Flask, render_template
from customers.views import customers_blueprints
from restaurants.views import restaurants_blueprints
from menus.views import menus_blueprints
from auth.views import auth_blueprints
import campus_eats

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24) 

app.register_blueprint(customers_blueprints, url_prefix='/customers')
app.register_blueprint(restaurants_blueprints, url_prefix='/restaurants')
app.register_blueprint(auth_blueprints)
app.register_blueprint(menus_blueprints, url_prefix='/menus')

# 登入頁面
@app.route('/')
def home():
    return render_template('auth/login.html')



if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug=True) #aws
    app.run(debug=True)
    