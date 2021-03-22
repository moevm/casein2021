from flask import Blueprint, render_template, request, redirect, render_template
from app.db_models import User, DBManager
from random import randint


bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    User(_id='admin', password='1234', full_name='Admin Admin').save()
    return render_template("index.html")


@bp.route('/users')
def users_page():
    return render_template("users.html", users=User.objects())


@bp.route('/user/create')
def user_create():
    return redirect(f'/user/update/{randint(0,10*10)}?new=true')


@bp.route('/user/<user_id>')
def user_page(user_id):
    user = DBManager.get_user(user_id)
    return render_template("user_id.html", user=user) if user else (f'Пользователь {user_id} не найден', 404)


@bp.route('/user/update/<user_id>', methods=['GET', 'POST'])
def user_update(user_id):
    """
    GET - страница редактирования пользователя (== страница создания пользователя с заполненными полями)
    POST - обновление пользователя
    """
    if request.method == 'GET':
        user = DBManager.get_user(user_id)
        if user or request.args.get('new'):
            return render_template("user_create.html", user=DBManager.get_user(user_id))
        else:
            return f"Пользователь {user_id} не найден", 404
    else:
        # пример словаря с клиента
        obj = {'_id': user_id, 'email': request.form['email'], 'password': request.form['password'], 'full_name': request.form['full_name']}
        user = User.from_object(obj)
        user.save()
        return redirect(f'/user/{user_id}')
