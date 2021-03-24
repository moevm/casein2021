import datetime
import pandas as pd

from uuid import uuid4
from json import loads as json_loads

from app.db_models import Course, Task, User, Solution, DBManager
from flask_security import login_required, current_user, roles_required
from flask import Blueprint, request, redirect, url_for, render_template, flash


bp = Blueprint('course', __name__, url_prefix='/course')

import logging
logger = logging.getLogger('root')


@bp.route('/')
@login_required
def course_index():
    return render_template("course.html", courses=Course.objects(name__ne=""))


@bp.route('/create')
@login_required
@roles_required('admin')
def course_create():
    new_course = Course(_id=str(uuid4()))
    new_course.save()
    return redirect(url_for('course.course_update', course_id=new_course._id, new=True))


@bp.route('/<course_id>')
@login_required
def course_page(course_id):
    course = DBManager.get_course(course_id)
    last_task = Solution.objects(user=current_user.pk, course=course_id).order_by('-datetime').first()
    return render_template("course_id.html", course=course, last_task=last_task) if course else (f'Курс {course_id} не найден', 404)

@bp.route('/<course_id>/task/<task_id>')
@login_required
def task_page(course_id, task_id):
    course = DBManager.get_course(course_id)
    task = DBManager.get_task(task_id)
    
    task_index = course.tasks.index(task)
    prev_task = course.tasks[task_index-1]._id if task_index > 0 else None
    next_task = course.tasks[task_index+1]._id if task_index < len(course.tasks)-1 else None
    
    next_url = url_for('course.task_page', course_id=course_id, task_id=next_task) \
        if next_task else url_for('course.course_page', course_id=course_id)
    
    return render_template(
        "task_passing.html", 
        course=course, 
        task=task, 
        next_url=next_url
        ) \
        if course and task and task in course.tasks \
        else (f'Задача {task_id} в курсе {course_id} не найдена', 404)


@bp.route('/check/<course_id>/<task_id>', methods=['POST'])
@login_required
def task_check(course_id, task_id):
    course = DBManager.get_course(course_id)
    task = DBManager.get_task(task_id)
    user_answer = json_loads(request.form['answer'])
    result = None
    if course and task:
        if task.task_type == 'test':
            true_ans = [answer[0] for answer in task.check['test']['answers']]
            user_ans = user_answer
            result = (true_ans == user_ans)
        logger.error(f'datetime: {datetime.datetime.utcnow()}')
        solution = Solution(course=course, task=task, user=current_user._get_current_object(), score=result * task.score, datetime=datetime.datetime.utcnow())
        solution.save()
        return {'result': result}
    else:
        return (f'Задача {task_id} в курсе {course_id} не найдена', 404)


@bp.route('/check/<course_id>', methods=['POST'])
@login_required
def course_check(course_id):
    course = DBManager.get_course(course_id)
    answers = json_loads(request.form['answers'])
    result = []
    if course:
        for index, task in enumerate(course.tasks):
            res = None
            if task.task_type == 'test':
                true_ans = [answer[0] for answer in task.check['test']['answers']]
                user_ans = answers[index][1]
                res = (true_ans == user_ans)
                result.append(res)
            solution = Solution(course=course, task=task, user=current_user._get_current_object(), score=res * task.score)
            solution.save()
        return {'result': result}
    else:
        return f"Курс {course_id} не найден", 404


@bp.route('/update/<course_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def course_update(course_id):
    """
    GET - страница редактирования курса (== страница создания курса с заполненными полями)
    POST - обновление курса
    """
    if request.method == 'GET':
        course = DBManager.get_course(course_id)
        if course or request.args.get('new'):
            return render_template("course_create.html", course=course)
        else:
            return f"Курс {course_id} не найден", 404
    else:
        obj = {'_id': course_id, 'name': request.form['name'], 'description': request.form['description']}
        course = Course.from_object(obj)
        course.save()
        return redirect(f'/course/{course_id}')


@bp.route('/remove/<course_id>', methods=['GET'])
@login_required
@roles_required('admin')
def course_remove(course_id):
    course = DBManager.get_course(course_id)
    if course:
        return_str = f"Курс '{course.name}' удален"
        course.delete()
        return return_str
    else:
        return f"Курс {course_id} не найден", 404


@bp.route('/update/<course_id>/task/create', methods=['GET'])
@login_required
@roles_required('admin')
def task_course_create(course_id):
    return redirect(url_for('course.task_course_update', course_id=course_id, task_id=uuid4(), new=True))


@bp.route('/update/<course_id>/task/<task_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def task_course_update(course_id, task_id):
    if request.method == 'GET':
        if not DBManager.get_course(course_id):
            return f"Курс {course_id} не найден", 404
        task = DBManager.get_task(task_id)
        if task or request.args.get('new'):
            return render_template("task_create.html", task=task, course_id=course_id, task_id=task_id, task_type=request.args.get('task_type', 'test'))
        else:
            return f"Задание {task} не найдено", 404
    else:
        task_info = request.form.to_dict()
        # logger.error(task_info)
        # logger.error(task_info.get('score'))
        task_info['_id'] = task_id
        if task_info['task_type'] == 'test':
            task_info['check'] = {'test': json_loads(task_info['check'])}
        task = Task.from_object(task_info).save()
        course = DBManager.get_course(course_id)
        if task in course.tasks:
            return 'задача в курсе'
        else:
            course.tasks.append(task)
            course.save()
            return 'добавили в курс'