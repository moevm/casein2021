from flask import Blueprint
from app.db_models import User


bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    User(_id='admin', password='1234', full_name='Admin Admin').save()
    return str(len(User.objects))

