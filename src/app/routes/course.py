from flask import Blueprint
from app.db_models import Course


bp = Blueprint('course', __name__, url_prefix='/course')


@bp.route('/')
def course_index():
    return str(len(Course.objects))


@bp.route('/<int:course_id>')
def course_page(course_id):
    return f'Get {course_id}: {Course.objects(_id=course_id).first()}'


@bp.route('/update/<int:course_id>')
def course_update(course_id):
    return f'Update {course_id}: {Course.objects(_id=course_id).first()}'

