import os
import sys
import json
import datetime
import subprocess
from uuid import uuid4
from cryptography.fernet import Fernet
from app.db_models import Course, Task
from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app
from flask_security import login_required, current_user, roles_required

import logging

logger = logging.getLogger('root')

bp = Blueprint('import_and_export', __name__, url_prefix='/import_and_export')

ALLOWED_COLLECTIONS = ['course', 'task', 'solution']

def import_collection_from_file(collection, filepath, host='mongo:27017', db='database'):
    subproc = subprocess.Popen([
            'mongoimport', 
            f'--host={host}', 
            f'--db={db}', 
            f'--collection={collection}',
            f'{filepath}'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    logger.error(subproc.communicate())


def export_collection_to_file(collection, filepath, host='mongo:27017', db='database'):
    subproc = subprocess.Popen([
            'mongoexport', 
            f'--host={host}', 
            f'--db={db}', 
            f'--collection={collection}',
            f'--out={filepath}',
            '--forceTableScan'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    logger.error(subproc.communicate())


def encrypt_file(filename, key, mode='r'):
    logger.error(f'{filename}')
    logger.error(f'{os.path.exists(filename)}')
    with open(filename, mode) as f:
        decrypted = f.read().encode()
    logger.error(f'{decrypted}')
    f = Fernet(key)
    encrypted = f.encrypt(decrypted)
    logger.error('finish enc1')
    return encrypted


def decrypt_file(filename, key, mode='rb'):
    encrypted = None
    with open(filename, mode) as f:
        encrypted = f.read()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted).decode('utf-8')
    return decrypted


def save_file(filename, string, mode='w'):
    with open(filename, mode) as f:
        f.write(string)


def encrypt_and_export(filepath, key, collection, need_ecrypt=True):
    export_collection_to_file(collection, filepath)
    if (need_ecrypt):
        logger.error('start enc')
        out = encrypt_file(filepath, key)
        save_file(filepath, out, mode='wb')
        logger.error('finish enc')
    

def decrypt_and_import(filepath, key, collection, need_decrypt=True):
    to_read = filepath
    logger.error(f'to_read: {to_read}')
    if need_decrypt:
        tmp_file = os.path.join(current_app.config['DUMP_FOLDER'], f'{uuid4()}.json')
        logger.error(f'tmp_file: {tmp_file}')
        out = decrypt_file(filepath, key)
        logger.error(f'out: {out}')
        save_file(tmp_file, out)
        to_read = tmp_file
        logger.error(f'to_read(new): {to_read}')
    logger.error(f'import')
    logger.error(f'to_read(new): {os.path.exists(to_read)}')
    import_collection_from_file(collection, to_read)
    logger.error(f'imported')
    
    if need_decrypt:
        os.remove(tmp_file)


@bp.before_app_first_request
def init_tasks_and_courses():
    if not os.path.exists(current_app.config['DUMP_FOLDER']):
        os.makedirs(current_app.config['DUMP_FOLDER'])
    key = os.environ.get('ENCRYPT_KEY').encode('utf-8')
    if len(Course.objects) == 0 and len(Task.objects) == 0:
        courses = os.path.join(current_app.config['DUMP_FOLDER'], 'init_course_enc.json')
        tasks = os.path.join(current_app.config['DUMP_FOLDER'], 'init_task_enc.json')
        if os.path.exists(courses) and os.path.exists(tasks):
            decrypt_and_import(tasks, key, 'task')
            decrypt_and_import(courses, key, 'course')



@bp.route('/export/', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def export_collection():
    if request.method == 'POST':
        base_path = current_app.config["DUMP_FOLDER"]
        dt = datetime.datetime.utcnow().strftime("%Y_%m_%dT%X:%f")
        collection = request.form.get("collection")
        filename = f'{collection}_{dt}.json'
        dump_path = os.path.join(base_path, filename)
        logger.error(f'{dump_path}')
        key = os.environ.get('ENCRYPT_KEY')
        encrypt_and_export(dump_path, key, collection, request.form.get('cypher'))
        return f'Коллекция {collection} экпортирована в файл {dump_path}'
    else:
        folder = current_app.config["DUMP_FOLDER"]
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        return render_template('import_export/export.html', collections=ALLOWED_COLLECTIONS)


@bp.route('/import/', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def import_collection():
    if request.method=='POST':
        logger.error(f'form:{request.form}') 
        dump_path = os.path.join(current_app.config["DUMP_FOLDER"], request.form.get('document'))
        logger.error(f'dump: {os.path.exists(dump_path)}, collection: {request.form.get("collection")}')
        if os.path.exists(dump_path) and request.form.get('collection'):
            key = os.environ.get('ENCRYPT_KEY')
            decrypt_and_import(dump_path, key, request.form.get('collection'), request.form.get('cypher'))
            return f"Коллекция {request.form.get('collection')} импортирована из файла {request.form.get('document')}"
        else:
            return ('fail', 500)
    else:
        folder = current_app.config["DUMP_FOLDER"]
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        return render_template('import_export/import.html', collections=ALLOWED_COLLECTIONS, files=files)