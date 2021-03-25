import numpy as np
import pandas as pd
import os
from flask import Blueprint, current_app, send_from_directory, render_template
from flask_security import login_required, roles_required
from app.db_models import Course, Task, User, Role, Solution, DBManager
import logging

logger = logging.getLogger('root')

bp = Blueprint('statistics', __name__, url_prefix='/statistics')

users_course_aggregate = [
    {"$group": {"_id":{"user":"$user", "course":"$course","task":"$task"}, "max":{"$max":"$score"}}}, 
    {"$group": {"_id":{'user':"$_id.user", 'course':"$_id.course"}, 'sum':{'$sum':"$max"}}},
    {'$replaceWith': {'user_id':"$_id.user", 'course_id':"$_id.course", 'score':"$sum"} },
    {'$set': {'user_id': {'$function': {'body': 'function(i) { return i.toString() }', 'args': [ "$user_id" ], 'lang': "js"}}}}
]

course_aggregate = [
    {'$project': {'_id' : 1 , 'name' : 1}},
]

course_score_aggregate = [
    { '$project': { '_id':1, 'name': 1, 'tasks':1 } },
    { '$unwind': "$tasks" }
]

tasks_score_aggregate = [
    { '$project': { '_id':1, 'score': 1 } }
]

@bp.before_app_first_request
def create_temp_folder():
    if not os.path.exists(current_app.config['TMP_FOLDER']):
        os.makedirs(current_app.config['TMP_FOLDER'])


@bp.route('/', methods=['GET'])
@login_required
@roles_required('admin')
def statistics_main():
    return render_template('statistics/statistics_main.html')


@bp.route('/courses', methods=['GET'])
@login_required
@roles_required('admin')
def courses_statistics():
    solutions = Solution.objects.aggregate(users_course_aggregate)
    user_role_id = Role.objects(name='user').first().pk
    
    users_aggregate = [
        { '$match': { 'roles': {'$in' :[user_role_id, '$roles']} }},
        {'$set': {'_id': {'$function': { 'body': 'function(i) { return i.toString() }', 'args': [ "$_id" ], 'lang': "js"}}}}
    ]
    users = User.objects.aggregate(users_aggregate)
    courses = Course.objects.aggregate(course_aggregate)

    courses_df = pd.DataFrame(courses).rename(columns={'_id':'course_id', 'name':'course_name'})
    courses_df = courses_df[courses_df.course_name != ""]
    users_df = pd.DataFrame(users).rename(columns={'_id':'user_id', 'full_name':'user_name'})
    solutions_df = pd.DataFrame(solutions)
    if solutions_df.shape[0] > 0:
        solution_stat = solutions_df \
            .merge(users_df, how='outer', on='user_id') \
            .merge(courses_df, how='outer', on='course_id') \
            [['score','user_name','course_name']]
        solutoin_pivot = pd.pivot_table(solution_stat, 'score', 'user_name', 'course_name', fill_value=0, dropna=False)
        diff = set(users_df.user_name).difference(set(solutoin_pivot.index))
        to_conc = pd.DataFrame(np.zeros((len(diff), solutoin_pivot.shape[1])), index=diff, columns=list(solutoin_pivot), dtype=np.int64)
        solutoin_pivot = solutoin_pivot.append(to_conc)
        return render_template('statistics/course_statistics.html', 
            table=solutoin_pivot.values, 
            users=solutoin_pivot.index.values.tolist(), 
            courses=list(solutoin_pivot))
    else:
        users = list(map(lambda x: x.get('full_name'), users))
        courses = list(map(lambda x: x.get('name'), courses))
        return render_template('statistics/course_statistics.html', 
            table=[[0]*courses_df.shape[0]]*users_df.shape[0], 
            users=users_df.user_name,
            courses=courses_df.course_name)


@bp.route('/course_score/<course_id>', methods=['GET'])
@login_required
def course_score(course_id):
    courses = DBManager.get_course(course_id)
    return str(sum(map(lambda x: x.score, courses.tasks)))


@bp.route('/courses_score', methods=['GET'])
@login_required
def user_statistic():
    courses = Course.objects.aggregate(course_score_aggregate)
    tasks = Task.objects.aggregate(tasks_score_aggregate)
    courses_df = pd.DataFrame(courses).rename(columns={'_id': 'course_id', 'tasks':'task_id'})
    tasks_df = pd.DataFrame(tasks).rename(columns={'_id': 'task_id'})
    
    scores_df = tasks_df.merge(courses_df, how='inner', on='task_id')
    res = scores_df.groupby('course_id').sum('score')
        
    return 'ok'