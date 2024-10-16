from flask import Blueprint

# 建立實體
restaurants_blueprints = Blueprint( 'restaurants', __name__, template_folder= 'templates/restaurants', static_folder='./static')

