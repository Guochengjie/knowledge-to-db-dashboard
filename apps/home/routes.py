# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us

"""

from apps.home import blueprint
from flask import render_template, request, redirect, abort, send_file
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.home.forms import TaskForm, JavaRelationPackageFrom
from apps.home.models import Task
from apps import db
from PackageGenerator import generate_java_package
import knowledge2db
import json
import sqlalchemy

import uuid
import os


def get_task_storage_path(task_uuid):
    if not task_uuid:
        return None
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', task_uuid)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def del_relation_by_entity_category(task_uuid, category):
    # delete all the relations that has the entity involved
    # get the entity table
    storage_path = get_task_storage_path(task_uuid)
    with open(os.path.join(storage_path, 'relation_tables.json'), 'r+') as f:
        relation_dict = json.load(f)
        for relation_general_category in list(relation_dict.keys()):
            for relation in list(relation_dict[relation_general_category].keys()):
                if category in relation:
                    del relation_dict[relation_general_category][relation]
        f.seek(0)
        json.dump(relation_dict, f)
        f.truncate()


def _verify_uuid_type_table(task_uuid, type_table):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    # check if type_table in ['entity', 'relation'], otherwise return 404
    if type_table not in ['entity', 'relation']:
        return render_template('home/page-404.html'), 404
    return task_obj, 200


def _get_table_attr(type_table, task_uuid, category, table):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    table_original = table
    storage_path = get_task_storage_path(task_uuid)
    # check if type_table in ['entity', 'relation'], otherwise return 404
    if type_table not in ['entity', 'relation']:
        return render_template('home/page-404.html'), 404
    # check if the table with category and table name exists, otherwise return 404
    if type_table == 'entity' and table[-5:] == '_info':
        table = 'base_attributes'
    if task_obj.custom_attr_type:
        custom_attr_type = json.loads(task_obj.custom_attr_type)
    else:
        custom_attr_type = {}
    if category not in custom_attr_type.keys():
        custom_attr_type = {}
    elif table not in custom_attr_type[category].keys():
        custom_attr_type = {}
    else:
        custom_attr_type = custom_attr_type[category][table]
    if task_obj.custom_index:
        custom_index = json.loads(task_obj.custom_index)
    else:
        custom_index = {}
    if category not in custom_index.keys():
        custom_index = {}
    elif table not in custom_index[category].keys():
        custom_index = {}
    else:
        custom_index = custom_index[category][table]
    if type_table == 'entity':
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r') as f, open(
                os.path.join(storage_path, 'entity_comments.json'), 'r') as f_comment:
            entity_dict = json.load(f)
            entity_comment_dict = json.load(f_comment)
            if category not in entity_dict:
                return render_template('home/page-404.html'), 404
            if table not in entity_dict[category]:
                return render_template('home/page-404.html'), 404

            return knowledge2db.tree_utilities.get_entity_table_attribute_json(entity_dict[category][table],
                                                                               custom_attr_type,
                                                                               entity_comment_dict[category][table],
                                                                               table_original, category,
                                                                               custom_index), 200
    elif type_table == 'relation':
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r') as f, open(
                os.path.join(storage_path, 'relation_comments.json'), 'r') as f_comment:
            relation_dict = json.load(f)
            relation_comment_dict = json.load(f_comment)
            for general_category in relation_dict:
                if category in relation_dict[general_category]:
                    if table not in relation_dict[general_category][category]:
                        return render_template('home/page-404.html'), 404
                    return knowledge2db.tree_utilities.get_relation_table_attribute_json(
                        relation_dict[general_category][category][table], custom_attr_type,
                        relation_comment_dict[general_category][category][table], table, category, custom_index), 200
            return render_template('home/page-404.html'), 404


def _get_attr_type_from_entity_info_table(task_uuid, category, attr):
    attr_json, _ = _get_table_attr('entity', task_uuid, category, category + '_info')
    for row in attr_json['rows']:
        if row['attribute'] == attr:
            return row['type']
    return None


@blueprint.route('/index')
@login_required
def index():
    return render_template('home/dashboard.html', segment='index')


@blueprint.route('/task/add', methods=['GET', 'POST'])
@login_required
def task_add():
    task_from = TaskForm()
    if task_from.validate_on_submit():
        # save files to disk
        task_uuid = str(uuid.uuid4())
        new_task = Task(title=task_from.title.data, description=task_from.description.data, task_uuid=task_uuid,
                        user_id=current_user.id, table_prefix=task_from.table_prefix.data)
        db.session.add(new_task)
        db.session.commit()
        # store the file in the upload folder relative to root of the project
        storage_path = get_task_storage_path(task_uuid)
        entity_opml_file = task_from.entity_opml_file.data
        entity_opml_file.save(os.path.join(storage_path, 'entity.opml'))
        relation_opml_file = task_from.relation_opml_file.data
        relation_opml_file.save(os.path.join(storage_path, 'relation.opml'))
        # now covert the opml file to json trees (suitable for echarts)
        entity_tree = knowledge2db.mindmap_loader.loader(os.path.join(storage_path, 'entity.opml'), "entity")
        with open(os.path.join(storage_path, 'entity_tree.json'), 'w') as f:
            f.write(json.dumps(entity_tree))
        relation_tree = knowledge2db.mindmap_loader.loader(os.path.join(storage_path, 'relation.opml'), "relation")
        with open(os.path.join(storage_path, 'relation_tree.json'), 'w') as f:
            f.write(json.dumps(relation_tree))
        # extract tables and columns from the above json
        tree_as_category = knowledge2db.tree_utilities.extract_children(entity_tree)
        tables, comments = knowledge2db.tree_utilities.extract_tables(tree_as_category)
        with open(os.path.join(storage_path, 'entity_tables.json'), 'w') as f:
            f.write(json.dumps(tables))
        with open(os.path.join(storage_path, 'entity_comments.json'), 'w') as f:
            f.write(json.dumps(comments))
        relation_tree_as_category = knowledge2db.tree_utilities.extract_children(relation_tree)
        relations, relation_comments = knowledge2db.tree_utilities.extract_relation_tables(relation_tree_as_category)
        with open(os.path.join(storage_path, 'relation_tables.json'), 'w') as f:
            f.write(json.dumps(relations))
        with open(os.path.join(storage_path, 'relation_comments.json'), 'w') as f:
            f.write(json.dumps(relation_comments))
        return redirect(f'/task')
    return render_template('home/add-task.html', segment='task_add', form=task_from)


@blueprint.route('/task/<task_uuid>')
@login_required
def task_detail(task_uuid):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    # TODO: create new template for task detail
    return render_template('home/task-detail.html', segment='task_detail', task=task_obj)


# list tasks for the current user
@blueprint.route('/task')
@login_required
def task():
    return render_template('home/task-list.html', segment='tasks')


@blueprint.route('/api/task/delete/<task_uuid>')
@login_required
def task_delete(task_uuid):
    task = Task.query.filter_by(uuid=task_uuid).first()
    if task is None:
        return render_template('home/page-404.html'), 404
    if task.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    db.session.delete(task)
    db.session.commit()
    # remove the folder
    storage_path = get_task_storage_path(task_uuid)
    if os.path.exists(storage_path):
        os.rmdir(storage_path)
    return redirect('/task')


# API to get the entity json tree for echarts
@blueprint.route('/api/task/echarts/<type_tree>/<task_uuid>')
@login_required
def api_task_tree(type_tree, task_uuid):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    storage_path = get_task_storage_path(task_uuid)
    if type_tree == 'entity':
        with open(os.path.join(storage_path, 'entity_tree.json'), 'r') as f:
            return f.read()
    elif type_tree == 'relation':
        with open(os.path.join(storage_path, 'relation_tree.json'), 'r') as f:
            return f.read()
    else:
        return render_template('home/page-404.html'), 404


# API to form json data needed for frontend table which shows a list of tables to be created
@blueprint.route('/api/task/tables/<type_table>/<task_uuid>')
@login_required
def task_tables(type_table, task_uuid):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return {'error': 'Task not found', 'code': 404, 'message': 'Not Found'}, 404
    if task_obj.user_id != current_user.id:
        return {'error': 'You are not authorized to access this resource', 'code': 403, 'message': 'Forbidden'}, 403
    storage_path = get_task_storage_path(task_uuid)
    if type_table == 'entity':
        # Example:
        # {"total":1,"totalNotFiltered":1,"rows":[{"category":"event","table":"event_info","attribute":["name","age"]}]}
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r') as f:
            entity_table = knowledge2db.tree_utilities.get_entity_table_json(json.load(f))
            with open(os.path.join(storage_path, 'api_entity_table.json'), 'w') as fp:
                fp.write(json.dumps(entity_table))
                return entity_table
    elif type_table == 'relation':
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r') as f:
            relation_table = knowledge2db.tree_utilities.get_relation_table_json(json.load(f))
            with open(os.path.join(storage_path, 'api_relation_table.json'), 'w') as fp:
                fp.write(json.dumps(relation_table))
                return relation_table
    else:
        return {'error': 'Task not found', 'code': 404, 'message': 'Not Found'}, 404


# API to remove selected tables
# format {"ids": [1,2,3]}
# the ids are auto generated by task_tables()
@blueprint.route('/api/task/tables/<type_table>/<task_uuid>/prune', methods=['post'])
def prune_tables(type_table, task_uuid):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    storage_path = get_task_storage_path(task_uuid)
    ids = request.form['ids'].split(',')
    try:
        ids = list(map(int, ids))
    except ValueError:
        return {'status': 'failed', 'message': 'invalid ids', 'code': 400}
    if type_table == 'entity':
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r+') as f, open(
                os.path.join(storage_path, 'api_entity_table.json'), 'r') as fp:
            entity_dict = json.load(f)
            entity_tables = json.load(fp)
            for table in entity_tables['rows']:
                if table['id'] in ids:
                    if table['table'][-5:] == '_info':
                        del entity_dict[table['category']]['base_attributes']
                        del_relation_by_entity_category(task_uuid, table['category'])
                    else:
                        del entity_dict[table['category']][table['table']]
            f.seek(0)
            json.dump(entity_dict, f)
            f.truncate()
        return {'status': 'success', 'message': 'pruned', 'code': 200}
    elif type_table == 'relation':
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r+') as f, open(
                os.path.join(storage_path, 'api_relation_table.json'), 'r') as fp:
            relation_dict = json.load(f)
            relation_tables = json.load(fp)
            for table in relation_tables['rows']:
                if table['id'] in ids:
                    del relation_dict[table['category']][table['relation']][table['table']]
            f.seek(0)
            json.dump(relation_dict, f)
            f.truncate()
        return {'status': 'success', 'message': 'pruned', 'code': 200}


# rename specific table
# format: {"category": "user", "old_name": "old", "new_name": new}
@blueprint.route('/api/task/tables/<type_table>/<task_uuid>/rename', methods=['post'])
def rename_table(type_table, task_uuid):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    storage_path = get_task_storage_path(task_uuid)
    category = request.form['category']
    old_name = request.form['old_name']
    new_name = request.form['new_name']
    if type_table == 'entity':
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r+') as f:
            entity_dict = json.load(f)
            entity_dict[category][new_name] = entity_dict[category][old_name]
            del entity_dict[category][old_name]
            f.seek(0)
            json.dump(entity_dict, f)
            f.truncate()
        with open(os.path.join(storage_path, 'entity_comments.json'), 'r+') as f:
            comments_dict = json.load(f)
            try:
                comments_dict[category][new_name] = comments_dict[category][old_name]
                del comments_dict[category][old_name]
                f.seek(0)
                json.dump(comments_dict, f)
                f.truncate()
            except KeyError:
                pass
        return {"message": "success", "code": 200}
    elif type_table == 'relation':
        relation = request.form['relation']
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r+') as f:
            relation_dict = json.load(f)
            relation_dict[category][relation][new_name] = relation_dict[category][relation][old_name]
            del relation_dict[category][relation][old_name]
            f.seek(0)
            json.dump(relation_dict, f)
            f.truncate()
        with open(os.path.join(storage_path, 'relation_comments.json'), 'r+') as f:
            comments_dict = json.load(f)
            try:
                comments_dict[category][relation][new_name] = comments_dict[category][relation][old_name]
                del comments_dict[category][relation][old_name]
                f.seek(0)
                json.dump(comments_dict, f)
                f.truncate()
            except KeyError:
                pass
        return {"message": "success", "code": 200}


# page to edit the attribute of a table
@blueprint.route('/task/tables/<type_table>/<task_uuid>/edit/<category>/<table>')
@login_required
def edit_table(type_table, task_uuid, category, table):
    task_obj, code = _verify_uuid_type_table(task_uuid, type_table)
    if code != 200:
        return task_obj
    storage_path = get_task_storage_path(task_uuid)
    # check if the table with category and table name exists, otherwise return 404
    if type_table == 'entity':
        table_original = table
        if table[-5:] == '_info':
            table = 'base_attributes'
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r') as f:
            entity_dict = json.load(f)
            if category not in entity_dict:
                return render_template('home/page-404.html'), 404
            if table not in entity_dict[category]:
                return render_template('home/page-404.html'), 404
        return render_template('home/task-edit-relation-table-attr.html', task_uuid=task_uuid, type_table=type_table,
                               category=category, table=table_original)
    elif type_table == 'relation':
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r') as f:
            relation_dict = json.load(f)
            found = False
            for general_category in relation_dict.keys():
                for relation in relation_dict[general_category].keys():
                    if table in relation_dict[general_category][relation].keys():
                        found = True
                        break
                if found:
                    break
            if not found:
                return render_template('home/page-404.html'), 404
        return render_template('home/task-edit-relation-table-attr.html', task_uuid=task_uuid, type_table=type_table,
                               category=category, table=table)


@blueprint.route('/task/java/<type_table>/<task_uuid>', methods=['get', 'post'])
@login_required
def generate_java_package_zip(type_table, task_uuid):
    task_obj, code = _verify_uuid_type_table(task_uuid, type_table)
    if code != 200:
        return task_obj
    form = JavaRelationPackageFrom()
    storage_path = get_task_storage_path(task_uuid)
    if request.method == 'POST' and form.validate_on_submit():
        if type_table == "relation":
            relation = form.relation.data
            attributes = form.attributes.data.split('|')
            config_dict = {
                'config': {
                    'db_engine': form.db_engine.data,
                    'db_port': int(form.db_port.data),
                    'db_server': form.db_host.data,
                    'db_username': form.db_username.data,
                    'db_password': form.db_password.data,
                    'db_name': form.db_name.data
                }
            }
            table_name = "_".join(relation.split(' / '))
            config_dict['relation'] = [{
                'table': table_name,
                'attribute_list': os.path.join(storage_path, table_name + '_attribute_list.json'),
                'db_table_name': task_obj.table_prefix + 'rel_' + table_name,
                'parties': relation.split(' / ')[0].split('_'),
                'foreign_key': [party + '_id' for party in relation.split(' / ')[0].split('_')],
                'attr_added_when_join_table': [
                    {
                        'attr_name': attribute_add.split(' / ')[1],
                        'from_table': task_obj.table_prefix + attribute_add.split(' / ')[0] + '_info',
                        'from_category': attribute_add.split(' / ')[0],
                        'type': _get_attr_type_from_entity_info_table(task_uuid, attribute_add.split(' / ')[0],
                                                                      attribute_add.split(' / ')[1])
                    } for attribute_add in attributes if attribute_add != ''
                ],
                'update_link_entity': [attribute_add.split(' / ')[0] for attribute_add in attributes if
                                       attribute_add != '']
            }]
            config_dict['entity'] = [
                {
                    'table': f'{party}_info',
                    'attribute_list': os.path.join(storage_path, f'{party}_info_attribute_list.json'),
                    'db_table_name': f"t_{party}_info",
                    'category': party
                } for party in relation.split(' / ')[0].split('_')
            ]
            # now, the most difficult part, we need to get indexed attributes
            try:
                custom_index_dict = json.loads(task_obj.custom_index)
                custom_type_dict = json.loads(task_obj.custom_attr_type)
            except TypeError:
                custom_index_dict = {}
                custom_type_dict = {}
            try:
                custom_index_dict = custom_index_dict[relation.split(' / ')[0]][relation.split(' / ')[1]]
                custom_indexed_attr = []
                custom_indexed_attr_list = []
                for index_list in custom_index_dict.values():
                    custom_indexed_attr.extend(index_list)
                custom_type_dict = custom_type_dict[relation.split(' / ')[0]][relation.split(' / ')[1]]
                for attr in custom_indexed_attr:
                    if attr in custom_type_dict.keys():
                        if custom_type_dict[attr].upper() == 'INT':
                            custom_indexed_attr_list.append({'attr_name': attr, 'attr_java_query_type': 'Integer'})
                        else:
                            custom_indexed_attr_list.append({'attr_name': attr, 'attr_java_query_type': 'String'})
                    else:
                        custom_indexed_attr_list.append({'attr_name': attr, 'attr_java_query_type': 'String'})
            except KeyError:
                custom_indexed_attr_list = []
            custom_indexed_attr_list += [{'attr_name': party + '_id', 'attr_java_query_type': 'String'} for party in
                                         relation.split(' / ')[0].split('_')]
            config_dict['relation'][0]['query_attr'] = custom_indexed_attr_list
            # now store the required json file to the storage path
            # entity json
            for party in relation.split(' / ')[0].split('_'):
                data, _ = _get_table_attr('entity', task_uuid, party, 'base_attributes')
                # write to os.path.join(storage_path, f'{party}_info_attribute_list.json')
                with open(os.path.join(storage_path, f'{party}_info_attribute_list.json'), 'w') as f:
                    json.dump(data, f)
            # relation json
            with open(os.path.join(storage_path, table_name + '_attribute_list.json'), 'w') as f:
                relation_data, _ = _get_table_attr('relation', task_uuid, relation.split(' / ')[0],
                                                   relation.split(' / ')[1])
                json.dump(relation_data, f)

            print(config_dict)
            zip_file_path = generate_java_package(config_dict, storage_path + '/java_package')
            # try to find the zip file and send it to the user
            if os.path.exists(zip_file_path):
                return send_file(zip_file_path, as_attachment=True)
            return abort(500, 'Failed to generate the java package')

    else:
        if type_table == "relation":
            # get the attributes of the task from entity_tables.json
            with open(os.path.join(storage_path, 'entity_tables.json'), 'r') as f:
                relation_dict = json.load(f)
                # get the base attributes of each category and store them in a dict
                attributes_dict = {}
                for category in relation_dict.keys():
                    if 'base_attributes' in relation_dict[category].keys():
                        attributes_dict[category] = [f"{category} / {attr}" for attr in
                                                     relation_dict[category]['base_attributes']]
            # open relation tables to get a list of available relations
            with open(os.path.join(storage_path, 'relation_tables.json'), 'r') as f:
                relation_dict = json.load(f)
                relations = []
                for general_category in relation_dict.keys():
                    for category in relation_dict[general_category].keys():
                        for relation in relation_dict[general_category][category].keys():
                            relations.append(f"{category} / {relation}")
            # add relations to form.relation field
            form.relation.choices = [(relation, relation) for relation in relations]
            return render_template("home/generate-relation-java-package.html", form=form,
                                   attributes_dict=attributes_dict)
        elif type_table == 'entity':
            return render_template('home/page-403.html'), 403


# page to edit tables of a task
@blueprint.route('/task/tables/<type_table>/<task_uuid>')
@login_required
def edit_tables(type_table, task_uuid):
    task_obj, code = _verify_uuid_type_table(task_uuid, type_table)
    if code != 200:
        return task_obj
    if type_table == 'entity':
        return render_template('home/task-edit-entity-tables.html', task_uuid=task_uuid,
                               segment='task_edit_entity_tables')
    elif type_table == 'relation':
        return render_template('home/task-edit-relation-tables.html', task_uuid=task_uuid,
                               segment='task_edit_relation_tables')


@blueprint.route('/api/task/tables/<type_table>/<task_uuid>/<category>/<table>')
@login_required
def get_table_attr(type_table, task_uuid, category, table):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    return _get_table_attr(type_table, task_uuid, category, table)


@blueprint.route('/api/task/attributes/<type_table>/<task_uuid>/<category>/<table>/prune', methods=['post'])
def prune_entity_attr(type_table, task_uuid, category, table):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    storage_path = get_task_storage_path(task_uuid)
    attrs = request.form['attrs'].split(',')
    print(request.data)
    if type_table == 'entity':
        table_original = table
        if table[-5:] == '_info':
            table = 'base_attributes'
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r+') as f, open(
                os.path.join(storage_path, 'entity_comments.json'), 'r+') as f_comment:
            entity_dict = json.load(f)
            entity_comment_dict = json.load(f_comment)
            if category not in entity_dict:
                return render_template('home/page-404.html'), 404
            if table not in entity_dict[category]:
                return render_template('home/page-404.html'), 404
            for attr in attrs:
                if attr in entity_dict[category][table]:
                    entity_dict[category][table].remove(attr)
                    try:
                        del entity_comment_dict[category][table_original][attr]
                    except KeyError:
                        pass
            f.seek(0)
            json.dump(entity_dict, f)
            f.truncate()
            f_comment.seek(0)
            json.dump(entity_comment_dict, f_comment)
            f_comment.truncate()
        return {'status': 'success', 'message': 'pruned', 'code': 200}
    elif type_table == 'relation':
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r+') as f, open(
                os.path.join(storage_path, 'relation_comments.json'), 'r+') as f_comment:
            relation_dict = json.load(f)
            relation_comment_dict = json.load(f_comment)
            found = False
            general_category = None
            for g_category in relation_dict.keys():
                if category in relation_dict[g_category].keys():
                    if table in relation_dict[g_category][category].keys():
                        found = True
                        general_category = g_category
                        break
            if not found:
                return render_template('home/page-404.html'), 404
            for attr in attrs:
                if attr in relation_dict[general_category][category][table]:
                    relation_dict[general_category][category][table].remove(attr)
                    try:
                        del relation_comment_dict[general_category][category][table][attr]
                    except KeyError:
                        pass
            f.seek(0)
            json.dump(relation_dict, f)
            f.truncate()
            f_comment.seek(0)
            json.dump(relation_comment_dict, f_comment)
            f_comment.truncate()
            # try to remove it from custom_index
            try:
                custom_index_dict = json.loads(task_obj.custom_index)
                for index_type, index_list in custom_index_dict[category][table].items():
                    if attr in index_list:
                        index_list.remove(attr)
                task_obj.custom_index = json.dumps(custom_index_dict)
                db.session.commit()
            except KeyError or TypeError:
                pass
        return {'status': 'success', 'message': 'pruned', 'code': 200}


@blueprint.route('/api/task/attributes/<type_table>/<task_uuid>/<category>/<table>/edit', methods=['post'])
def edit_entity_attr(type_table, task_uuid, category, table):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    storage_path = get_task_storage_path(task_uuid)
    data_type_new = request.form['data_type']
    data_type_old = request.form['data_type_old']
    constraint_new = request.form['constraints']
    special_constraint = request.form['special_constraint']
    attr_old = request.form['attr_old']
    attr_new = request.form['attr_new']
    comment = request.form['comment']
    if type_table == 'entity':
        table_original = table
        if table[-5:] == '_info':
            table = 'base_attributes'
        with open(os.path.join(storage_path, 'entity_tables.json'), 'r+') as f, open(
                os.path.join(storage_path, 'entity_comments.json'), 'r+') as f_comment:
            entity_dict = json.load(f)
            entity_comment_dict = json.load(f_comment)
            if category not in entity_dict:
                return render_template('home/page-404.html'), 404
            if table not in entity_dict[category]:
                return render_template('home/page-404.html'), 404
            # rename the attribute if the name is changed
            if attr_old != attr_new:
                entity_dict[category][table].remove(attr_old)
                entity_dict[category][table].append(attr_new)
                try:
                    entity_comment_dict[category][table][attr_new] = comment
                    del entity_comment_dict[category][table][attr_old]
                except KeyError:
                    pass
            else:
                # change the comment, however, the comment can be empty, so we need to check if the key exists
                try:
                    entity_comment_dict[category][table][attr_new] = comment
                except KeyError:
                    print("Error occur when changing the comment")
            # write the changes to the file
            f.seek(0)
            json.dump(entity_dict, f)
            f.truncate()
            f_comment.seek(0)
            json.dump(entity_comment_dict, f_comment)
            f_comment.truncate()
    elif type_table == 'relation':
        with open(os.path.join(storage_path, 'relation_tables.json'), 'r+') as f, open(
                os.path.join(storage_path, 'relation_comments.json'), 'r+') as f_comment:
            relation_dict = json.load(f)
            relation_comment_dict = json.load(f_comment)
            found = False
            general_category = None
            for g_category in relation_dict.keys():
                if category in relation_dict[g_category].keys():
                    if table in relation_dict[g_category][category].keys():
                        found = True
                        general_category = g_category
                        break
            if not found:
                return render_template('home/page-404.html'), 404
            # rename the attribute if the name is changed
            if attr_old != attr_new:
                relation_dict[general_category][category][table].remove(attr_old)
                relation_dict[general_category][category][table].append(attr_new)
                try:
                    del relation_comment_dict[general_category][category][table][attr_old]
                except KeyError:
                    pass
            try:
                relation_comment_dict[general_category][category][table][attr_new] = comment
            except KeyError:
                print("Error occur when changing the comment")

            # write the changes to the file
            f.seek(0)
            json.dump(relation_dict, f)
            f.truncate()
            f_comment.seek(0)
            json.dump(relation_comment_dict, f_comment)
            f_comment.truncate()
    # change the data type if the data type is changed
    # the data should be stored in the following format
    # task_obj.custom_attr_type[category][table][attr_new] = data_type_new
    # however, the dict can be empty, so we need to check if the key exists
    if data_type_old != data_type_new or constraint_new or attr_old != attr_new:
        if task_obj.custom_attr_type is None:
            custom_attr_type = {}
        else:
            custom_attr_type = json.loads(task_obj.custom_attr_type)
        if category not in custom_attr_type:
            custom_attr_type[category] = {}
        if table not in custom_attr_type[category]:
            custom_attr_type[category][table] = {}
        if constraint_new is None or constraint_new == '':
            custom_attr_type[category][table][attr_new] = data_type_new
        else:
            custom_attr_type[category][table][attr_new] = data_type_new + ' ' + constraint_new
        task_obj.custom_attr_type = json.dumps(custom_attr_type)
        db.session.commit()
    if special_constraint != "":
        special_constraint = special_constraint.upper()
        if task_obj.custom_index:
            special_constraint_dict = json.loads(task_obj.custom_index)
        else:
            special_constraint_dict = {}
        if category not in special_constraint_dict:
            special_constraint_dict[category] = {}
        if table not in special_constraint_dict[category]:
            special_constraint_dict[category][table] = {}
        if special_constraint not in special_constraint_dict[category][table]:
            special_constraint_dict[category][table][special_constraint] = [attr_new]
        else:
            special_constraint_dict[category][table][special_constraint].append(attr_new)
        task_obj.custom_index = json.dumps(special_constraint_dict)
        db.session.commit()
    return {'status': 'success', 'message': 'pruned', 'code': 200}


# api to get sql query for creating tables (all in one)
@blueprint.route('/api/get_sql_query/<task_uuid>')
@login_required
def get_sql_query(task_uuid):
    task_obj = Task.query.filter_by(uuid=task_uuid).first()
    if task_obj is None:
        return render_template('home/page-404.html'), 404
    if task_obj.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    storage_path = get_task_storage_path(task_uuid)
    try:
        custom_attr_type = json.loads(task_obj.custom_attr_type)
    except TypeError:
        custom_attr_type = {}
    try:
        custom_index_dict = json.loads(task_obj.custom_index)
    except TypeError:
        custom_index_dict = {}
    if not task_obj.table_prefix:
        table_prefix = "t_"
    else:
        table_prefix = task_obj.table_prefix
    with open(os.path.join(storage_path, 'entity_tables.json'), 'r') as f, open(
            os.path.join(storage_path, 'relation_tables.json'), 'r') as f_relation, open(
        os.path.join(storage_path, 'entity_comments.json'), 'r') as f_comment, open(
        os.path.join(storage_path, 'relation_comments.json'), 'r') as f_relation_comment:
        entity_dict = json.load(f)
        relation_dict = json.load(f_relation)
        entity_comment_dict = json.load(f_comment)
        relation_comment_dict = json.load(f_relation_comment)
        create_tables = ["-- Entity Tables:"]
        create_tables += knowledge2db.sql_generator.create_table_by_category(entity_dict, entity_comment_dict,
                                                                             custom_column_type=custom_attr_type,
                                                                             custom_index=custom_index_dict,
                                                                             table_prefix=table_prefix)
        create_tables.append("-- Relation Tables:")
        create_tables += knowledge2db.sql_generator.create_relation_table(relation_dict, relation_comment_dict,
                                                                          custom_column_type=custom_attr_type,
                                                                          custom_index=custom_index_dict,
                                                                          table_prefix=table_prefix)

    return {'status': 'success', 'message': create_tables, 'code': 200}


@blueprint.route('/api/task/list')
@login_required
def api_list_task():
    all_tasks = Task.query.filter_by(user_id=current_user.id, del_flag=False).all()
    result = {"rows": []}
    for user_task in all_tasks:
        result['rows'].append({
            "uuid": user_task.uuid,
            "title": user_task.title,
            "description": user_task.description
        })
    result['total'] = len(result['rows'])
    result['totalNotFiltered'] = len(result['rows'])
    return result


@blueprint.route('/api/task/delete', methods=['POST'])
@login_required
def api_delete_task():
    # delete a list of tasks based on uuid
    # get the list of uuid from uuid_list then split by comma
    uuid_list = request.form.get('uuid_list').split(',')
    for task_uuid in uuid_list:
        task_obj = Task.query.filter_by(uuid=task_uuid).first()
        if task_obj is None:
            return render_template('home/page-404.html'), 404
        if task_obj.user_id != current_user.id:
            return render_template('home/page-403.html'), 403
        task_obj.del_flag = True
    db.session.commit()
    return {'status': 'success', 'message': 'deleted', 'code': 200}


@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
