import mongoengine as me


class User(me.Document):
    _id = me.StringField(primary_key=True)
    password = me.StringField()
    full_name = me.StringField()
    # role = me.IntField()  # должно задаваться flask securiry
    progress  = me.DictField() 


class Task(me.Document):
    _id = me.StringField(primary_key=True)
    name = me.StringField()
    condition = me.StringField()
    task_type = me.IntField()
    some_info  = me.DictField() 


class Course(me.Document):
    _id = me.StringField(primary_key=True)
    name = me.StringField()
    tasks = me.ListField(me.ReferenceField(Task))
    users = me.ListField(me.ReferenceField(User))
    some_info = me.DictField() 