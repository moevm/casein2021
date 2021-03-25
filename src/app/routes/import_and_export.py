import os
import sys
import json
import datetime
import subprocess
from uuid import uuid4
from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app
from flask_security import login_required, current_user, roles_required

import logging

logger = logging.getLogger('root')

bp = Blueprint('import_and_export', __name__, url_prefix='/import_and_export')

ALLOWED_COLLECTIONS = ['course', 'task', 'solution']

@bp.before_app_first_request
def init_tasks_and_courses():
    pass

@bp.route('/export/<collection>', methods=['GET'])
@login_required
@roles_required('admin')
def export_collection(collection):
    dump_path = os.path.join(current_app.config["DUMP_FOLDER"], f'{collection}_{datetime.datetime.utcnow().strftime("%Y_%m_%dT%X:%f")}.json')
    subproc = subprocess.Popen([
            'mongoexport', 
            '--host=mongo:27017', 
            '--db=database', 
            f'--collection={collection}',
            f'--out={dump_path}',
            '--forceTableScan'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,)
    logger.error(subproc.communicate())
    return f'Коллекция {collection} экпортирована в файл {dump_path}'


def import_collection_from_file(collection, filepath, host='mongo:27017', db='database'):
    subproc = subprocess.Popen([
            'mongoimport', 
            f'--host={host}', 
            f'--db={db}', 
            f'--collection={collection}',
            f'{filename}'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    logger.error(subproc.communicate())


@bp.route('/import/', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def import_collection():
    if request.method=='POST':
        # dump_path = os.path.join(current_app.config["DUMP_FOLDER"], collection+datetime.datetime.utcnow().strftime("%Y_%m_%dT%X:%f")+".json")
        return f'collection'
    else:
        folder = current_app.config["DUMP_FOLDER"]
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        return render_template('import.html', collections=ALLOWED_COLLECTIONS, files=files)