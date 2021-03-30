import numpy as np
import pandas as pd
import os
from flask import Blueprint, current_app, send_from_directory, render_template
from flask_security import login_required, roles_required, roles_accepted, current_user
from app.db_models import Course, Task, User, Role, Solution, AdapterEmployees, DBManager
import logging

logger = logging.getLogger('root')

bp = Blueprint('statistics', __name__, url_prefix='/statistics')

def get_adapter_employees(adapter_id):
    adapter_employees = AdapterEmployees.objects(adapter=adapter_id)
    employees = AdapterEmployees.objects.aggregate([
        {'$match': {'adapter': adapter_id}},
        {'$project': {'_id':0, 'employee':1}},
        {'$set': {'employee': {'$function': {'body': 'function(i) { return i.toString() }', 'args': [ "$employee" ], 'lang': "js"}}}}
    ])
    return employees

def get_users_course_aggregate():
    return [
        {"$group": {"_id":{"user":"$user", "course":"$course","task":"$task"}, "max":{"$max":"$score"}}}, 
        {"$group": {"_id":{'user':"$_id.user", 'course':"$_id.course"}, 'sum':{'$sum':"$max"}}},
        {'$replaceWith': {'user_id':"$_id.user", 'course_id':"$_id.course", 'score':"$sum"} },
        {'$set': {'user_id': {'$function': {'body': 'function(i) { return i.toString() }', 'args': [ "$user_id" ], 'lang': "js"}}}}
    ]

def get_users_aggregate():
    user_role_id = Role.objects(name='user').first().pk
    return [
        {'$match': { 'roles': {'$in' :[user_role_id, '$roles']} }},
        {'$project': {'_id': 1, 'full_name':1}},
        {'$set': {'_id': {'$function': { 'body': 'function(i) { return i.toString() }', 'args': [ "$_id" ], 'lang': "js"}}}}
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

@bp.route('/', methods=['GET'])
@roles_accepted('admin', 'adapter')
def statistics_main():
    return render_template('statistics/statistics_main.html', courses=Course.objects(name__ne="").only('_id', 'name'))

pd.set_option('display.max_columns', 10)


@bp.route('/courses', methods=['GET'])
@roles_accepted('admin', 'adapter')
def courses_statistics():
    solutions = Solution.objects.aggregate(get_users_course_aggregate())
    users = User.objects.aggregate(get_users_aggregate())
    courses = Course.objects.aggregate(course_aggregate)

    courses_df = pd.DataFrame(courses).rename(columns={'_id':'course_id', 'name':'course_name'})
    courses_df = courses_df[(courses_df.course_name != "") & (courses_df.course_name != 'Большая пятерка')]
    users_df = pd.DataFrame(users).rename(columns={'_id':'user_id', 'full_name':'user_name'})
    solutions_df = pd.DataFrame(solutions)
    
    if solutions_df.shape[0] > 0:
        solution_stat = solutions_df.merge(users_df, how='outer', on='user_id')
        if current_user.has_role('adapter'):
            adapter_emp = pd.DataFrame(get_adapter_employees(current_user.pk))\
                .rename(columns={'employee': 'user_id'})
            solution_stat = solution_stat.merge(adapter_emp, on='user_id', how='right')
        adapter_emp_names = solution_stat.user_name.dropna().unique()
        solution_stat = solution_stat \
            .merge(courses_df, how='outer', on='course_id') \
            [['score','user_name','course_name']]
        solution_stat.score = solution_stat.score.fillna(0)
        solution_pivot = pd.pivot_table(solution_stat, 'score', 'user_name', 'course_name', fill_value=0, dropna=False)
        diff = None
        if solution_pivot.shape[0] == 0:
            solution_pivot.columns = [col[1] for col in solution_pivot.columns]
        if current_user.has_role('adapter'):
            diff = set(adapter_emp_names).difference(set(solution_pivot.index))
        else:
            diff = set(users_df.user_name).difference(set(solution_pivot.index))
        
        to_conc = pd.DataFrame(np.zeros((len(diff), solution_pivot.shape[1])), index=diff, columns=list(solution_pivot), dtype=np.int64)
        solution_pivot = solution_pivot.append(to_conc)
        return render_template('statistics/course_statistics.html', 
            table=solution_pivot.values, 
            users=solution_pivot.index.values.tolist(), 
            titles=list(solution_pivot))
    else:
        users = list(map(lambda x: x.get('full_name'), users))
        courses = list(map(lambda x: x.get('name'), courses))
        return render_template('statistics/course_statistics.html', 
            table=[[0]*courses_df.shape[0]]*users_df.shape[0], 
            users=users_df.user_name,
            titles=courses_df.course_name)

def get_users_tasks_for_course(course_id):
    return [
        {'$match': {'course': course_id}},
        {'$group': {'_id':{'user_id':"$user", 'task_id':"$task"}, 'max':{'$max':"$score"}}},
        {'$replaceWith': {'user_id':"$_id.user_id", 'task_id':"$_id.task_id", 'score':"$max"}},
        {'$set': {'user_id': { '$function': { 'body': 'function(i) { return i.toString() }', 'args': [ "$user_id" ], 'lang': "js"}}}}
    ]

@bp.route('/course_statisic/<course_id>', methods=['GET'])
@login_required
@roles_accepted('admin', 'adapter')
def course_tasks_statistics(course_id):
    course = Course.objects(_id=course_id).only('name').first()
    if not course:
        return (f"Неверный id курса", 400)
    solutions = Solution.objects.aggregate(get_users_tasks_for_course(course_id))
    solutions = pd.DataFrame(solutions)
    
    
    users = User.objects.aggregate(get_users_aggregate())
    users = pd.DataFrame(users).rename(columns={'_id':'user_id', 'full_name':'user_name'})

    tasks = [{'task_id': it["_id"], 'task_name':it["name"]} for it in Course.objects(_id=course_id)[0].tasks]
    tasks = pd.DataFrame(tasks)
    

    if solutions.shape[0] > 0:
        solution_stat = solutions \
            .merge(users, how='inner', on='user_id') \
            .merge(tasks, how='outer', on='task_id') \
            [['score','user_name','task_name']]
        # logger.error('stat')
        # logger.error(f'{list(solution_stat)}')
        # logger.error(f'{solution_stat}')
        solution_pivot = pd.pivot_table(solution_stat, 'score', 'user_name', 'task_name', fill_value=0, dropna=False)
        diff = set(users.user_name).difference(set(solution_pivot.index))
        to_conc = pd.DataFrame(np.zeros((len(diff), solution_pivot.shape[1])), index=diff, columns=list(solution_pivot), dtype=np.int64)
        solution_pivot = solution_pivot.append(to_conc)
        return render_template('statistics/course_statistics.html', 
            table=solution_pivot.values, 
            users=solution_pivot.index.values.tolist(), 
            titles=list(solution_pivot))
    else:

        return render_template('statistics/course_statistics.html', 
            table=[[0]*tasks.shape[0]]*users.shape[0], 
            users=users.user_name,
            titles=tasks.task_name,
            course_name=course.name)
    

@bp.route('/course_score/<course_id>', methods=['GET'])
@login_required
def course_score(course_id):
    courses = DBManager.get_course(course_id)
    return str(sum(map(lambda x: x.score, courses.tasks)))


@bp.route('/courses_sum_score', methods=['GET'])
@login_required
def user_statistic():
    courses = Course.objects.aggregate(course_score_aggregate)
    tasks = Task.objects.aggregate(tasks_score_aggregate)
    courses_df = pd.DataFrame(courses).rename(columns={'_id': 'course_id', 'tasks':'task_id'})
    tasks_df = pd.DataFrame(tasks).rename(columns={'_id': 'task_id'})
    
    scores_df = tasks_df.merge(courses_df, how='inner', on='task_id')
    res = scores_df.groupby('course_id').sum('score')
    logger.error(res)
    return 'ok'