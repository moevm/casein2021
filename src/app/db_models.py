from flask_security import UserMixin, RoleMixin
import mongoengine as me
import datetime

class NoRequiredField(Exception):
    pass


class Role(me.Document, RoleMixin):
    name = me.StringField(max_length=50, unique=True)
    description = me.StringField(max_length=255)

    def __unicode__(self):
        return self.name


class User(me.Document, UserMixin):
    _id = me.StringField(primary_key=True)
    email = me.StringField(max_length=30)
    password = me.StringField(max_length=30)
    full_name = me.StringField(max_length=50)
    confirmed_at = me.DateTimeField(default=datetime.datetime.utcnow())
    roles = me.ListField(me.ReferenceField(Role), default=[])

    @staticmethod
    def from_object(user_object):
        for key in ('_id', 'email', 'password', 'full_name'):
            if key not in user_object:
                raise NoRequiredField(f'Отсутствует необходимое поле пользователя: {key}')

        return User(_id=user_object.get('_id'),
                email=user_object.get('email'),
                password=user_object.get('password'),
                full_name=user_object.get('full_name'))


class AdapterEmployees(me.EmbeddedDocument):
    user = me.ReferenceField(User)
    users = me.ListField(me.ReferenceField(User), default=[])


class Task(me.Document):
    _id = me.StringField(primary_key=True)
    name = me.StringField()
    condition = me.StringField()
    task_type = me.StringField(max_length=5)
    check = me.DictField() 

    @staticmethod
    def from_object(task_object):
        for key in ('_id', 'name', 'condition', 'task_type', 'check'):
            if key not in task_object:
                raise NoRequiredField(f'Отсутствует необходимое поля задания: {key}')

        return Task(_id=task_object.get('_id'),
                name=task_object.get('name'),
                condition=task_object.get('condition'),
                task_type=task_object.get('task_type'),
                check=task_object.get('check'))


class Course(me.Document):
    _id = me.StringField(primary_key=True)
    name = me.StringField(default="")
    description = me.StringField(default="")
    tasks = me.ListField(me.ReferenceField(Task), default=[])
    users = me.ListField(me.ReferenceField(User), default=[])
    datetime = me.DateTimeField(default=datetime.datetime.utcnow())
    some_info = me.DictField() 

    @staticmethod
    def from_object(course_object):
        course = DBManager.get_course(course_object['_id']) 
        course_object['tasks'] = course.tasks if course else []
        
        for key in ('_id', 'name', 'tasks', 'description'):
            if key not in course_object:
                raise NoRequiredField(f'Отсутствует необходимое поле курса: {key}')

        return Course(_id=course_object.get('_id'),
                name=course_object.get('name'),
                tasks=course_object.get('tasks'),
                description=course_object.get('description'))


class Solution(me.Document):
    _id = me.StringField(primary_key=True)
    task = me.ReferenceField(Task)
    user = me.ReferenceField(User)
    score = me.IntField(default=0)
    datetime = me.DateTimeField(default=datetime.datetime.utcnow())


class DBManager:
    
    @staticmethod
    def get_course(course_id):
        return Course.objects(_id=course_id).first()

    @staticmethod
    def get_task(task_id): return Task.objects(_id=task_id).first()

    @staticmethod
    def get_user(user_id): return User.objects(_id=user_id).first()
