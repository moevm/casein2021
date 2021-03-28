from random import randint

from app.db_models import User, Role, Solution, Course, AdapterEmployees, DBManager
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

def get_aggregation_user_course_stat(user):
    bf = Course.objects(name='Большая пятерка').first()['_id']
    return [
        {'$match': {'user': user.pk, 'course': { '$ne': bf }}}, 
        {'$group': {'_id':{'course':"$course",'task':"$task"}, 'max':{'$max':"$score"}}},
        {'$group': {'_id':"$_id.course", 'sum':{'$sum':"$max"}}}
    ]

def get_aggregation_adapters(adapter_id):
    return [
        { '$match': { 'roles': {'$in' :[adapter_id, '$roles']}}},
        { '$project': {'full_name':1}}
    ]

@bp.route('/user/<user_id>', methods=['GET', 'POST'])
@login_required
def user_page(user_id):
    user = DBManager.get_user(user_id)
    if not user:
        return (f'Пользователь {user_id} не найден', 404)
    if request.method == 'GET':
        current_user_has_user_role = any([role['name'] == 'user' for role in user.roles])
        user_adapter = AdapterEmployees.objects(employee=user.pk).first()
        adapter_id = Role.objects(name="adapter").first()
        if not adapter_id:
            return 'No adapter role', 500
        adapter_id = adapter_id.pk
        adapters = User.objects.aggregate(get_aggregation_adapters(adapter_id))
        logger.error(f'adapters: {adapters}')
        #TODO: display next
        user_courses_stat = Solution.objects.aggregate(get_aggregation_user_course_stat(user))
        return render_template("user_id.html", 
            user=user, 
            current_user_has_user_role=current_user_has_user_role,
            user_adapter=user_adapter,
            adapters=list(adapters)) \
            if user else (f'Пользователь {user_id} не найден', 404)
    else:
        logger.error('POSTED')
        employee = AdapterEmployees.objects(employee=user.pk).first()
        logger.error(f'{employee}')
        if current_user.has_role('adapter'):
            logger.error('has adapter role')
            if not employee:
                ad_emp = AdapterEmployees(employee=user.pk, adapter=current_user.pk)
                ad_emp.save()
                logger.error(f'{ad_emp}')
                return 'saved'
            else:
                return 'У пользователя уже есть адаптер', 400
        elif current_user.has_role('admin'):
            logger.error('has admin role')
            if not employee:
                ad_emp = AdapterEmployees(employee=user.pk, adapter=request.form.get('adapter'))
                ad_emp.save()
                logger.error(f'{ad_emp}')
            else:
                # logger.error(employee.employee)
                # logger.error(employee.adapter)
                adapter = DBManager.get_user(request.form.get('adapter'))
                employee.update(set__adapter=adapter)
            return 'saved'
        else:
            return 'Forbidden', 403
        
            

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
