from flask import Blueprint, request
from app.db_models import Course, Task, get_course


bp = Blueprint('course', __name__, url_prefix='/course')


@bp.route('/')
def course_index():
    return str(len(Course.objects))

@bp.route('/create')
def course_create():
    return 'Создание курса'


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
    if request.method == 'POST':
        return get_course(course_id)
    else:
        # пример словаря с клиента
        obj = {'_id': course_id, 'name': 'name', 'tasks': [dict(_id='_id1', name='name', condition='condition', task_type=1, check={}),
            dict(_id='_id2', name='name', condition='condition', task_type=1, check={})]
        }
        course = Course.from_object(obj)
        course.save()
        return course.to_json()

