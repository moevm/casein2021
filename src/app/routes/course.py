from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_security import login_required, current_user, roles_required
from app.db_models import Course, Task, Solution, DBManager
from uuid import uuid4
from json import loads as json_loads

bp = Blueprint('course', __name__, url_prefix='/course')


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
    import logging
    logger = logging.getLogger('root')
    logger.error('/create ' + str(type(new_course._id)))
    return redirect(url_for('course.course_update', course_id=new_course._id, new=True))


@bp.route('/<course_id>')
@login_required
def course_page(course_id):
    course = DBManager.get_course(course_id)
    return render_template("course_id.html", course=course) if course else (f'Курс {course_id} не найден', 404)

import logging
logger = logging.getLogger('root')

@bp.route('/check/<course_id>', methods=['POST'])
@login_required
def course_check(course_id):
    course = DBManager.get_course(course_id)
    logger.error(f'user: {current_user}')
    logger.error(f'course: {course}')
    answers = json_loads(request.form['answers'])
    result = []
    if course:
        for index, task in enumerate(course.tasks):
            logger.error(f'course tasks: ({index}){task}')
            res = None
            if task.task_type == 'test':
                true_ans = [answer[0] for answer in task.check['test']['answers']]
                user_ans = answers[index][1]
                res = (true_ans == user_ans)
                result.append(res)
            logger.error(f'before solution')
            solution = Solution(course=course, task=task, user=current_user, score=res * task.score)
            logger.error(f'solution {solution}')
            solution.save()
            logger.error(f'solution saved')
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
        import logging
        logger = logging.getLogger('root')
        logger.error('/update/<course_id> ' + str(DBManager.get_course(course_id)._id))
        if course or request.args.get('new'):
            return render_template("course_create.html", course=course)
        else:
            return f"Курс {course_id} не найден", 404
    else:
        # пример словаря с клиента
        #tasks=[]
        #for i in range(0, int(request.form['tasks_count'])):
        #    task = dict(_id='_id'+ str(i), name=request.form['name_' + str(i)], condition=request.form['condition_' + str(i)], task_type=request.form['type_' + str(i)], check={'test':request.form['check_' + str(i)]})
        #    tasks.append(task)
        obj = {'_id': course_id, 'name': request.form['course_name'], 'description': request.form['course_description']}
        course = Course.from_object(obj)
        course.save()
        return redirect(f'/course/{course_id}')


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
        logger.error(task_info)
        logger.error(task_info.get('score'))
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