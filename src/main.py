from flask import Flask
from flask_mongoengine import MongoEngine

from app.routes.index import bp as index_bp


def get_db(): return db


app = Flask(__name__)

app.template_folder = 'app/web/templates'
app.static_folder = 'app/web/static'
app.config['MONGODB_SETTINGS'] = {
    'db':'database',
    'host':'mongo',
    'port':27017
}
app.register_blueprint(index_bp)


db = MongoEngine(app)


app.run(debug=True, host='0.0.0.0')
