import pandas as pd
import os
from flask import Blueprint, current_app, send_from_directory, render_template
from flask_security import login_required, roles_required
from app.db_models import Course, Task, User, Solution
import logging

logger = logging.getLogger('root')

bp = Blueprint('statistics', __name__, url_prefix='/statistics')

aggregation_users_course_stat = [
    {"$group": {"_id":{"user":"$user", "course":"$course","task":"$task"}, "max":{"$max":"$score"}}}, 
    {"$group": {"_id":{'user':"$_id.user", 'course':"$_id.course"}, 'sum':{'$sum':"$max"}}},
    {'$replaceWith': {'user_id':"$_id.user", 'course_id':"$_id.course", 'score':"$sum"} },
    {'$set': {'user_id': {'$function': {'body': 'function(i) { return i.toString() }', 'args': [ "$user_id" ], 'lang': "js"}}}}
]
users_aggregate = [
    {'$project': {'_id' : 1 , 'full_name' : 1}},
    {'$set': {'_id': {'$function': { 'body': 'function(i) { return i.toString() }', 'args': [ "$_id" ], 'lang': "js"}}}}
]
course_aggregate = [
    {'$project': {'_id' : 1 , 'name' : 1}},
]

@bp.before_app_first_request
def create_temp_folder():
    if not os.path.exists(current_app.config['TMP_FOLDER']):
        os.makedirs(current_app.config['TMP_FOLDER'])


@bp.route('/', methods=['GET'])
@login_required
@roles_required('admin')
def users_list():
    with open(os.path.join(current_app.config['TMP_FOLDER'], 'test.txt'), 'w', encoding='utf-8') as file:
        for task in Task.objects.only('name'):
            file.write(str(task.to_json()))
    return send_from_directory(current_app.config['TMP_FOLDER'], 'test.txt')


@bp.route('/courses', methods=['GET'])
@login_required
@roles_required('admin')
def course_statistics():
    solutions = Solution.objects.aggregate(aggregation_users_course_stat)
    users = User.objects.aggregate(users_aggregate)
    courses = Course.objects.aggregate(course_aggregate)

    solutions_df = pd.DataFrame(solutions)
    users_df = pd.DataFrame(users).rename(columns={'_id':'user_id', 'full_name':'user_name'})
    courses_df = pd.DataFrame(courses).rename(columns={'_id':'course_id', 'name':'course_name'})

    solution_stat = solutions_df.merge(users_df, how='right', on='user_id').merge(courses_df, how='right', on='course_id')[['score','user_name','course_name']]

    solutoin_pivot = pd.pivot_table(solution_stat, 'score', 'user_name', 'course_name', fill_value=0)
    
    return render_template('course_statistics.html', 
        table=solutoin_pivot.values, 
        users=solutoin_pivot.index.values.tolist(), 
        courses=list(solutoin_pivot))
