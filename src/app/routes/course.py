from flask import Blueprint, request, redirect, url_for, render_template
from app.db_models import Course, Task, get_course
from random import randint

bp = Blueprint('course', __name__, url_prefix='/course')


@bp.route('/')
def course_index():
    return render_template("course.html")

@bp.route('/create')
def course_create():
    return redirect(f'/course/update/{randint(0,10*10)}?new=true')


@bp.route('/<course_id>')
def course_page(course_id):
    course = get_course(course_id)
    return course.to_json() if course else (f'Курс {course_id} не найден', 404)


@bp.route('/update/<course_id>', methods=['GET', 'POST'])
def course_update(course_id):
    """
    GET - страница редактирования курса (== страница создания курса с заполненными полями)
    POST - обновление курса
    """
    if request.method == 'GET':
        course = get_course(course_id)
        if course or request.args.get('new'):
            return render_template("course_create.html", course=get_course(course_id))
        else:
            return f"Курс {course_id} не найден", 404
    else:
        # пример словаря с клиента
        tasks=[]
        for i in range(1, int(request.form['tasks_count'])+1):
            task = dict(_id='_id'+ str(i), name=request.form['name_' + str(i)], condition=request.form['condition_' + str(i)], task_type=request.form['type_' + str(i)], check={'test':request.form['check_' + str(i)]})
            tasks.append(task)
        obj = {'_id': course_id, 'name': request.form['course_name'], 'tasks': tasks}
        course = Course.from_object(obj)
        course.save()
        return redirect(f'/course/{course_id}')

