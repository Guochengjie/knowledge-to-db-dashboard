import json
from jinja2 import Template, Environment, PackageLoader, select_autoescape
import os
from datetime import datetime
import re
import shutil


# function to conver snake case to camel case
def _snake_to_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def _snake_to_capital(snake_str):
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


def _get_current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _remove_quotes(string):
    return re.sub(r"'", '', string)


# function to convert mysql type to Java type
def _mysql_to_java(mysql_type):
    mysql_type = mysql_type.lower()
    if mysql_type == "tinyint":
        return "byte"
    elif mysql_type == "smallint":
        return "short"
    elif mysql_type == "mediumint" or mysql_type == "int":
        return "Integer"
    elif mysql_type == "bigint":
        return "long"
    elif mysql_type == "float":
        return "float"
    elif mysql_type == "double":
        return "double"
    elif mysql_type == "decimal":
        return "java.math.BigDecimal"
    elif mysql_type == "date":
        return "java.time.LocalDate"
    elif mysql_type == "datetime" or mysql_type == "timestamp":
        return "java.time.LocalDateTime"
    elif mysql_type == "time":
        return "java.time.LocalTime"
    elif mysql_type == "year":
        return "java.time.Year"
    elif mysql_type == "char" or "varchar" in mysql_type or mysql_type == "text" or mysql_type == "mediumtext" or mysql_type == "longtext":
        return "String"
    elif mysql_type == "binary" or mysql_type == "varbinary" or mysql_type == "blob" or mysql_type == "mediumblob" or mysql_type == "longblob":
        return "byte[]"
    else:
        return "Object"


def _render_entity_info_po_dao_xml(j2_env, template_path, attribute_json_path, table_name):
    with open(attribute_json_path) as f:
        data = json.load(f)
        print(64, data)
        data['name'] = table_name
        data['fields'] = data['rows']
        del data['rows']
        data['column_list'] = [attr['attribute'] for attr in data['fields']]

    with open(template_path, 'r') as f:
        template = j2_env.from_string(f.read())
        return template.render(table=data)


def _render_application_local_properties(j2_env, template_path, config):
    with open(template_path, 'r') as f:
        template = j2_env.from_string(f.read())
        return template.render(config=config)


def _render_table_template(j2_env, template_path, attribute_json_path, meta):
    with open(attribute_json_path) as f:
        data = json.load(f)
        meta['column_list'] = [attr['attribute'] for attr in data['rows']]
        with open(template_path, 'r') as f:
            template = j2_env.from_string(f.read())
            return template.render(attrs=data['rows'], meta=meta)


def _render_enum(j2_env, template_path, title, options):
    with open(template_path, 'r') as f:
        template = j2_env.from_string(f.read())
        return template.render(title=title, options=options)


def _write_output_file(output_folder, file_name, content):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    with open(os.path.join(output_folder, file_name), 'w') as f:
        f.write(content)


def generate_java_package(config_dict, output_dir):
    # setup jinja2 environment
    env = Environment(
        autoescape=select_autoescape()
    )

    env.filters['snake_to_camel'] = _snake_to_camel
    env.filters['mysql_to_java'] = _mysql_to_java
    env.filters['snake_to_capital'] = _snake_to_capital
    env.filters['remove_quotes'] = _remove_quotes
    env.globals.update(get_current_datetime=_get_current_datetime)

    # copy the template project to the destination folder (output_dir)
    # use absolute path to the package folder
    package_root = os.path.dirname(__file__)

    template_project_folder = os.path.join(os.path.dirname(__file__), 'knowledge_system_project_template')
    print(package_root, template_project_folder, output_dir)

    shutil.copytree(template_project_folder, output_dir, dirs_exist_ok=True)

    for t in config_dict['entity']:
        table_name = t['table']
        attribute_list = t['attribute_list']
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/resources/mapper'),
                           _snake_to_capital(table_name) + 'PODao.xml',
                           _render_entity_info_po_dao_xml(env, os.path.join(package_root,
                                                                            'templates/EntityInfoPODao.xml.j2'),
                                                          attribute_list, table_name))

        _write_output_file(
            os.path.join(output_dir, 'knowledge_system/src/main/resources/config'), 'application-local.properties',
            _render_application_local_properties(env, os.path.join(package_root,
                                                                   'templates/application-local.properties.j2'),
                                                 config_dict['config']))

    for t in config_dict['entity']:
        # po
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/po'),
                           _snake_to_capital(t['table']) + 'PO.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/EntityInfoPO.java.j2'),
                                                  t['attribute_list'], t))

        # dao
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/dao'),
                           _snake_to_capital(t['table']) + 'Dao.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/EntityInfoDao.java.j2'),
                                                  t['attribute_list'], t))

        # serivce impl
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/service/impl'),
                           _snake_to_capital(t['table']) + 'ServiceImpl.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/EntityInfoServiceImpl.java.j2'),
                                                  t['attribute_list'], t))

        # service
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/service'),
                           _snake_to_capital(t['table']) + 'Service.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/EntityInfoService.java.j2'),
                                                  t['attribute_list'], t))

    for t in config_dict['relation']:
        # po
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/po'),
                           _snake_to_capital(t['table']) + 'PO.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/RelationPO.java.j2'),
                                                  t['attribute_list'], t))

        # dto
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/dto'),
                           'Insert' + _snake_to_capital(t['table']) + 'DTO.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/InsertRelationDTO.java.j2'),
                                                  t['attribute_list'], t))

        # dao
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/dao'),
                           _snake_to_capital(t['table']) + 'Dao.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/RelationDao.java.j2'),
                                                  t['attribute_list'], t))

        # param
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/param'),
                           'Get' + _snake_to_capital(t['table']) + 'Param.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/GetRelationParam.java.j2'),
                                                  t['attribute_list'], t))
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/param'),
                           'Insert' + _snake_to_capital(t['table']) + 'Param.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/InsertRelationParam.java.j2'),
                                                  t['attribute_list'], t))
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/param'),
                           'Update' + _snake_to_capital(t['table']) + 'Param.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/UpdateRelationParam.java.j2'),
                                                  t['attribute_list'], t))

        # VO
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/domain/vo'),
                           _snake_to_capital(t['table']) + 'VO.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/RelationVO.java.j2'),
                                                  t['attribute_list'], t))

        # operation/impl
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/operation/impl'),
                           _snake_to_capital(t['table']) + 'OperationImpl.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/RelationOperationImpl.java.j2'),
                                                  t['attribute_list'], t))

        # operation
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/operation'),
                           _snake_to_capital(t['table']) + 'Operation.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/RelationOperation.java.j2'),
                                                  t['attribute_list'], t))

        # service
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/service'),
                           _snake_to_capital(t['table']) + 'Service.java',
                           _render_table_template(env, os.path.join(package_root, 'templates/RelationService.java.j2'),
                                                  t['attribute_list'], t))

        # service impl
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/service/impl'),
                           _snake_to_capital(t['table']) + 'ServiceImpl.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/RelationServiceImpl.java.j2'),
                                                  t['attribute_list'], t))

        # relation PO dao xml
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/resources/mapper'),
                           _snake_to_capital(t['table']) + 'PODao.xml',
                           _render_table_template(env, os.path.join(package_root, 'templates/RelationPODao.xml.j2'),
                                                  t['attribute_list'], t))

        # controller
        _write_output_file(os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/controller'),
                           _snake_to_capital(t['table']) + 'Controller.java',
                           _render_table_template(env,
                                                  os.path.join(package_root, 'templates/RelationController.java.j2'),
                                                  t['attribute_list'], t))
        # now, extract enum from relation table.
        # try to find the column which is int type and the comment is not null or empty
        attribute_list_path = os.path.join(output_dir, t['attribute_list'])
        with open(attribute_list_path, 'r') as f:
            attribute_list = json.load(f)
            for attr in attribute_list['rows']:
                if attr['type'].lower() == 'int' and attr['comment'] is not None and attr['comment'] != '':
                    list_regex = re.compile(r"\d+\.\s'(.*?)'")
                    # Find all matches of the pattern in the input string
                    list_items = list_regex.findall(attr['comment'])
                    if len(list_items) != 0:
                        # Print the resulting list
                        print(attr['attribute'], list_items)
                        _write_output_file(
                            os.path.join(output_dir, 'knowledge_system/src/main/java/com/jd/icity/koala/common/enums'),
                            _snake_to_capital(attr['attribute']) + 'Enum.java',
                            _render_enum(env, os.path.join(package_root, 'templates/RelationTypeEnum.java.j2'),
                                         attr['attribute'], list_items))

        # now zip the output dir
        shutil.make_archive(os.path.join(output_dir, 'knowledge_system'), 'zip', output_dir + '/knowledge_system')
        return os.path.join(output_dir, 'knowledge_system.zip')
