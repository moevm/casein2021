from flask import Blueprint, render_template
from app.db_models import User


bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    User(_id='admin', password='1234', full_name='Admin Admin').save()
    return render_template("index.html")

@bp.route('/user/create')
def user_create():
    return 1
