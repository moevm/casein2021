import pandas as pd

from random import randint

from app.db_models import User, Role, Solution, Course, DBManager
from flask import Blueprint, render_template, request, redirect, render_template, current_app
from flask_security import login_required, current_user, roles_required, LoginForm, url_for_security


bp = Blueprint('index', __name__)

@bp.before_app_first_request
def init_roles_and_users():
    if not current_app.user_datastore.get_user('sotrudnik@rosatom.ru'):
        current_app.user_datastore.create_role(name="user")
        current_app.user_datastore.create_user(email='sotrudnik@rosatom.ru',password='sotrudnik', full_name='sotrudnik name', roles=['user'])
    if not current_app.user_datastore.get_user('administrator@rosatom.ru'):
        current_app.user_datastore.create_role(name="admin")
        current_app.user_datastore.create_user(email='administrator@rosatom.ru', password='password', full_name='administrator name', roles=['admin'])
    if not current_app.user_datastore.get_user('adapter@rosatom.ru'):
        current_app.user_datastore.create_role(name="adapter")
        current_app.user_datastore.create_user(email='adapter@rosatom.ru',password='adapter', full_name='adapter name', roles=['adapter'])


@bp.context_processor
def login_context():
    return {
        'url_for_security': url_for_security,
        'login_user_form': LoginForm(),
    }


@bp.route('/')
def index():
    return render_template("index.html")


@bp.route('/users')
@login_required
@roles_required('admin')
def users_page():
    return render_template("users.html", users=User.objects())


@bp.route('/user/create')
def user_create():
    return redirect(f'/user/update/{randint(0,10*10)}?new=true')

import logging

logger = logging.getLogger('root')

def compute_big_five(user):
    course = Course.objects(name='Большая пятерка').first()
    big_five_user = [
        {'$match':{'course':course._id, 'user':user.pk}},
        {'$group': {"_id":'$task', 'datetime':{'$max':"$datetime"}, 'score': {'$first':'$score'}}},
        {'$project': {'_id':1, 'score':1}}
    ]
    user_response = pd.DataFrame(Solution.objects.aggregate(big_five_user))
    if len(course.tasks) != user_response.shape[0]:
        logger.error('Пройдены не все задачи')
        return
    out = map(lambda task: {
            '_id': task._id,
            'inverse': task.check.get('inverse'),
            'direction': task.check.get('direction')
        }, course.tasks)
    tasks = pd.DataFrame(out).merge(user_response, how='outer', on='_id')
    tasks.loc[tasks['inverse'], 'score'] = 4-tasks.loc[tasks['inverse'], 'score']
    logger.error(f'{tasks}')
    res = tasks[['direction','score']] \
        .groupby('direction') \
        .mean()
    res.score = (res.loc[:, 'score'] * 25).astype(int) # / 4 (max value) * 100
    logger.error(f'{res}')
    return res

def compute_user_statistic(user):
    aggregation_user_course_stat = [
        {'$match': {'user': user.pk}},
        {'$group': {'_id':{'course':"$course",'task':"$task"}, 'max':{'$max':"$score"}}},
        {'$group': {'_id':"$_id.course", 'sum':{'$sum':"$max"}}}
    ]
    res = Solution.objects.aggregate(aggregation_user_course_stat)
    logger.error(f'res: {list(res)}')
    return res

@bp.route('/user/<user_id>')
@login_required
def user_page(user_id):
    user = DBManager.get_user(user_id)
    # res = compute_user_statistic(user)
    compute_big_five(user)
    return render_template("user_id.html", user=user) if user else (f'Пользователь {user_id} не найден', 404)


@bp.route('/user/update/<user_id>', methods=['GET', 'POST'])
@login_required
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
