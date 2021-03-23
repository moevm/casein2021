from flask import Flask
from flask_mongoengine import MongoEngine
from flask_admin import Admin
from flask_admin.base import MenuLink
from flask_admin.contrib.mongoengine import ModelView
from wtforms.fields import HiddenField
from flask_security import Security, MongoEngineUserDatastore, current_user

from app.db_models import User, Role

from app.routes.index import bp as index_bp
from app.routes.course import bp as course_bp
from app.routes.files import bp as files_bp

import logging
logger = logging.getLogger('root')


def get_db(): return db
def get_datastore(): return user_datastore

app = Flask(__name__)

app.template_folder = 'app/web/templates'
app.static_folder = 'app/web/static'
app.config['MONGODB_SETTINGS'] = {
    'db':'database',
    'host':'mongo',
    'port':27017
}
app.config['SECRET_KEY'] = 'SECRET_KEY'
app.config['SECURITY_PASSWORD_SALT'] = 'some arbitrary super secret string'

app.register_blueprint(index_bp)
app.register_blueprint(course_bp)
app.register_blueprint(files_bp)

db = MongoEngine(app)

app.user_datastore = MongoEngineUserDatastore(db, User, Role)
app.security = Security(app, app.user_datastore)


def is_hidden_field_filter(field):
    return isinstance(field, HiddenField)

class AdminUserView(ModelView):
    column_exclude_list = ('password')
    # form_overrides = dict(password=HiddenField)

    def is_accessible(self):
        if current_user.is_authenticated and Role.objects(name='admin').first() in current_user.roles:
            return True
        return False


admin = Admin(app, template_mode='bootstrap3')
admin.add_view(AdminUserView(User))
admin.add_view(AdminUserView(Role))
admin.add_link(MenuLink(name='Logout', endpoint='security.logout'))

app.run(debug=True, host='0.0.0.0')
