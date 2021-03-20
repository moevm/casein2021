import mongoengine as me

class NoRequiredField(Exception):
    pass


class User(me.Document):
    _id = me.StringField(primary_key=True)
    password = me.StringField()
    full_name = me.StringField()
    # role = me.IntField()  # должно задаваться flask securiry
    progress  = me.DictField() 


class Task(me.EmbeddedDocument):
    _id = me.StringField(primary_key=True)
    name = me.StringField()
    condition = me.StringField()
    task_type = me.IntField()
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
    name = me.StringField()
    tasks = me.EmbeddedDocumentListField(Task)
    users = me.ListField(me.ReferenceField(User))
    some_info = me.DictField() 

    @staticmethod
    def from_object(course_object):
        for key in ('_id', 'name', 'tasks'):
            if key not in course_object:
                raise NoRequiredField(f'Отсутствует необходимое поле курса: {key}')

        return Course(_id=course_object.get('_id'),
                name=course_object.get('name'),
                tasks=[Task.from_object(task) for task in course_object['tasks']])


def get_course(course_id): return Course.objects(_id=course_id).first()