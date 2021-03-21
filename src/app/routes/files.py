import os
import sys
from uuid import uuid4
from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app
from app.db_models import File
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger('root')

bp = Blueprint('files', __name__, url_prefix='/files')

# TODO: to config
UPLOAD_FOLDER = 'app/web/static/documents/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'}
logger.error(f"UPLOAD_FOLDER: {UPLOAD_FOLDER}")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=['GET', 'POST'])
def files_list():
    return render_template("files.html", files=File.objects)

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    return redirect(f'/files/update/{str(uuid4())}?new=true')

@bp.route('/remove/<file_id>', methods=['GET', 'POST'])
def remove_file(file_id):
    file = get_file(file_id)
    if file:
        if os.path.exists(os.path.join(UPLOAD_FOLDER,file.filename)):
            os.remove(os.path.join(UPLOAD_FOLDER,file.filename))
        file.delete()
    return redirect(f'/files/')

@bp.route('/update/<file_id>', methods=['GET', 'POST'])
def update_file(file_id):
    """
    GET - страница редактирования файла (== страница создания файла с заполненными полями)
    POST - обновление файла
    """
    if request.method == 'POST':
        existing = get_file(file_id)
        
        logger.error(f'is existing: {existing}')
        logger.error(f'request.files: {request}')
        if not existing: # add
            if 'file' not in request.files:
                return 'No file part'
            file = request.files['file']
            if file.filename == '':
                return 'No selected file'
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f'{uuid4()}.{ext}'
                db_file = File(_id=file_id, title=request.form.get('title'), filename=filename)
                db_file.save()
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                return redirect(url_for('files.files_list'))
        else: # update
            if 'file' in request.files:
                file = request.files['file']
                logger.error(f'POST, is existing: {file}')
                if file and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    os.remove(os.path.join(UPLOAD_FOLDER, existing.filename))
                    filename = f'{uuid4()}.{ext}'
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    existing.filename = filename
            existing.title=request.form.get('title')
            existing.save()
            return redirect(url_for('files.files_list'))

    elif request.method == 'GET':
        file = get_file(file_id)
        if file or request.args.get('new'):
            logger.error(f'GET, is existing: {file}')
            return render_template("upload_documents.html", file=file)
        else:
            return f"Файл {file_id} не найден", 404


def get_file(file_id): return File.objects(_id=file_id).first()