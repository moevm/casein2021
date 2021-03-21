import os

from flask import Blueprint, request, redirect, url_for, render_template
from app.db_models import File
from werkzeug.utils import secure_filename

bp = Blueprint('files', __name__, url_prefix='/files')

# TODO: to config
UPLOAD_FOLDER = './statis/documents/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=['GET', 'POST'])
def files_list():
    return str(len(File.objects))

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):  
            filename = secure_filename(file.filename)
            db_file = File(title=request.form.get('title'), filename=filename)
            db_file.save()
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('files.files_list'))
    
    return render_template("upload_documents.html")