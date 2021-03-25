import os
import sys
import datetime
import subprocess
from uuid import uuid4
from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app, send_from_directory
from flask_security import login_required, current_user, roles_required
from app.db_models import File, DBManager
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger('root')

bp = Blueprint('files', __name__, url_prefix='/files')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.before_app_first_request
def create_upload_folder():
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])

@bp.route('/', methods=['GET', 'POST'])
@login_required
def files_list():
    return render_template("files.html", files=File.objects)

@bp.route('/<file_id>', methods=['GET', 'POST'])
@login_required
def get_file(file_id):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], file_id)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def upload_file():
    return redirect(f'/files/update/{str(uuid4())}?new=true')

@bp.route('/remove/<file_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def remove_file(file_id):
    file = DBManager.get_file(file_id)
    if file:
        if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)):
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
        file.delete()
    return redirect(f'/files/')

@bp.route('/update/<file_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def update_file(file_id):
    """
    GET - страница редактирования файла (== страница создания файла с заполненными полями)
    POST - обновление файла
    """
    if request.method == 'POST':
        existing = DBManager.get_file(file_id)
        if not existing: # add
            if 'file' not in request.files:
                return 'No file part'
            file = request.files['file']
            if file.filename == '':
                return 'No selected file'
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filepath = f'{uuid4()}.{ext}'
                db_file = File(_id=file_id, title=request.form.get('title'), filename=file.filename,filepath=filepath)
                db_file.save()
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filepath))
                return redirect(url_for('files.files_list'))
            else:
                return 'Неразрешенное разрешение файла!'
        else: # update
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], existing.filepath))
                    filepath = f'{file_id}.{ext}'
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filepath))
                    existing.filename = file.filename
                    existing.filepath = filepath
            existing.title=request.form.get('title')
            existing.save()
            return redirect(url_for('files.files_list'))

    elif request.method == 'GET':
        file = DBManager.get_file(file_id)
        if file or request.args.get('new'):
            logger.error(f'GET, is existing: {file}')
            return render_template("upload_documents.html", file=file)
        else:
            return f"Файл {file_id} не найден", 404
