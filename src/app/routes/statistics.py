import os
from flask import Blueprint, current_app, send_from_directory
from flask_security import login_required, roles_required
from app.db_models import Task
import logging

logger = logging.getLogger('root')

bp = Blueprint('statistics', __name__, url_prefix='/statistics')


@bp.before_app_first_request
def create_temp_folder():
    if not os.path.exists(current_app.config['TMP_FOLDER']):
        os.makedirs(current_app.config['TMP_FOLDER'])


@bp.route('/', methods=['GET'])
@login_required
@roles_required('admin')
def users_list():
    with open(os.path.join(current_app.config['TMP_FOLDER'], 'test.txt'), 'w', encoding='utf-8') as file:
        for task in Task.objects.only('name'):
            file.write(str(task.to_json()))
    return send_from_directory(current_app.config['TMP_FOLDER'], 'test.txt')
