from knowledge2db import config
import re
from .tree_utilities import convert_index_dict_to_attr_index_dict


def _generate_attr_col_sql(attribute, comment_str, custom_column_type={}):
    # default VARCHAR(32)
    # if date in attribute.lower(), use DATE
    # if time in attribute.lower(), use DATETIME
    # if place or location or address in attribute.lower(), use VARCHAR(256)
    if attribute.lower() in custom_column_type.keys():
        return f"`{attribute}` {custom_column_type[attribute.lower()]} {comment_str}, \n"
    elif "date" in attribute.lower():
        return f"`{attribute}` DATE {comment_str}, \n"
    elif "time" in attribute.lower():
        return f"`{attribute}` DATETIME {comment_str}, \n"
    elif "place" in attribute.lower() or "location" in attribute.lower() or "address" in attribute.lower():
        return f"`{attribute}` VARCHAR(256) {comment_str}, \n"
    else:
        return f"`{attribute}` VARCHAR(32) {comment_str}, \n"


def create_db_user(username, password, host="localhost"):
    return f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}';"


def create_db(username, database_name, user_host="localhost"):
    return f"CREATE DATABASE {database_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON {database_name}.* TO '{username}'@'{user_host}';"


def drop_databases(db_list):
    sql_commands = []
    for db in db_list:
        sql_commands.append(f"DROP DATABASE IF EXISTS {db};")
    return sql_commands


def create_db_by_category(username, categories, prefix=config.db_prefix, user_host="localhost"):
    # categories is a list of categories
    # prefix is the prefix of the database name
    # return a list of sql commands
    sql_commands = []
    # if the input is a dict, extract its keys
    if isinstance(categories, dict):
        categories = list(categories.keys())
    for category in categories:
        database_name = f"{prefix}{category}"
        sql_commands.append(create_db(username, database_name, user_host=user_host))
    return sql_commands


def create_secondary_table(table_name, attributes, comments, primary_key, foreign_key, foreign_table,
                           custom_column_type={}, custom_index={}):
    # add a primary key (id), which is auto-incremented
    # add a create_time and update_time
    # limit the table name to 64 characters
    # FOR ENTITIES ONLY
    table_name = table_name[:64]
    sql = f"CREATE TABLE {table_name} ({primary_key} INT NOT NULL, \n"
    for attribute in attributes:
        try:
            comment_str = re.sub(r"'", '"', comments[attribute])
        except KeyError:
            comment_str = ""
        if comment_str != "":
            comment_str = f"COMMENT '{comment_str}'"
        # default VARCHAR(32)
        # if date in attribute.lower(), use DATE
        # if time in attribute.lower(), use DATETIME
        # if place or location or address in attribute.lower(), use VARCHAR(256)
        if attribute.lower() in custom_column_type.keys():
            sql += f"`{attribute}` {custom_column_type[attribute.lower()]} {comment_str}, \n"
        elif "date" in attribute.lower():
            sql += f"`{attribute}` DATE {comment_str}, \n"
        elif "time" in attribute.lower():
            sql += f"`{attribute}` DATETIME {comment_str}, \n"
        elif "place" in attribute.lower() or "location" in attribute.lower() or "address" in attribute.lower():
            sql += f"`{attribute}` VARCHAR(256) {comment_str}, \n"
        else:
            sql += f"`{attribute}` VARCHAR(32) {comment_str}, \n"
    sql += ("create_time DATETIME DEFAULT CURRENT_TIMESTAMP, \n"
            "create_user VARCHAR(32) DEFAULT 'system', \n"
            "create_app VARCHAR(32) DEFAULT 'system',"
            "modify_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, \n"
            "modify_user VARCHAR(32) DEFAULT 'system', \n"
            "modify_app VARCHAR(32) DEFAULT 'system',"
            f"PRIMARY KEY ({primary_key}), \n"
            f"FOREIGN KEY ({primary_key}) REFERENCES {foreign_table} ({foreign_key}) "
            "ON DELETE CASCADE ON UPDATE CASCADE")
    # add custom index
    for attr in custom_index:
        # custom_index = {'attr': 'INDEX'}
        sql += f", \n{custom_index[attr]} ({attr})"
    sql += ");\n"
    return sql


def create_info_table(table_name, attributes, comments, table_prefix, custom_column_type={}, custom_index={}):
    # use base attributes in each category to form a info table
    # FOR ENTITIES ONLY
    sql = f"CREATE TABLE {table_prefix}{table_name}_info (id INT NOT NULL AUTO_INCREMENT, \n"
    for attribute in attributes:
        try:
            comment_str = re.sub(r"'", '"', comments[attribute])
        except KeyError:
            comment_str = ""
        if comment_str != "":
            # trim the comment string to 1000 characters
            comment_str = comment_str[:1000]
            comment_str = f"COMMENT '{comment_str}'"
        sql += _generate_attr_col_sql(attribute, comment_str, custom_column_type)
    sql += (f"{table_name}_id VARCHAR(36) UNIQUE NOT NULL, \n"
            "create_time DATETIME DEFAULT CURRENT_TIMESTAMP, \n"
            "create_user VARCHAR(32) DEFAULT 'system', \n"
            "create_app VARCHAR(32) DEFAULT 'system', \n"
            "modify_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, \n"
            "modify_user VARCHAR(32) DEFAULT 'system', \n"
            "modify_app VARCHAR(32) DEFAULT 'system', \n"
            "del_stat INT DEFAULT 0, \n"
            "version_no INT DEFAULT 0, \n"
            "PRIMARY KEY (id)")
    for attr in custom_index:
        # custom_index = {'attr': 'INDEX'}
        sql += f", \n{custom_index[attr]} ({attr})"
    sql += ");\n"
    return sql


def create_table_by_category(tables: dict, comments: dict, db_prefix: object = config.db_prefix, table_prefix: str = config.table_prefix,
                             custom_column_type: dict = {}, custom_index: dict = {}) -> dict:
    # tables is a dictionary of tables
    # comments is a dictionary of comments
    # prefix is the prefix of the database name
    # return a list of sql commands
    # FOR ENTITIES ONLY
    name_of_base_attributes = ""
    if config.naming == "camel":
        name_of_base_attributes = "baseAttributes"
    elif config.naming == "lower_case_with_underscores":
        name_of_base_attributes = "base_attributes"
    sql_commands = []
    for category in tables:
        if name_of_base_attributes not in tables[category]:
            continue
        # now create the primary table
        try:
            custom_column_type_dict = custom_column_type[category][name_of_base_attributes]
        except KeyError:
            custom_column_type_dict = {}

        try:
            custom_index_dict = convert_index_dict_to_attr_index_dict(custom_index[category][name_of_base_attributes])
        except KeyError:
            custom_index_dict = {}
        sql_commands.append(create_info_table(f"{category.lower()}", tables[category][name_of_base_attributes],
                                              comments[category][name_of_base_attributes],
                                              custom_column_type=custom_column_type_dict, table_prefix=table_prefix,
                                              custom_index=custom_index_dict))
        for table in tables[category]:
            if table == name_of_base_attributes:
                continue
            try:
                custom_column_type_dict = custom_column_type[category][table]
            except KeyError:
                custom_column_type_dict = {}
            try:
                custom_index_dict = custom_index[category][table]
            except KeyError:
                custom_index_dict = {}
            sql_commands.append(
                create_secondary_table(f"{table_prefix}{category.lower()}_{table}", tables[category][table],
                                       comments[category][table], f"{category}_id", "id",
                                       f"{table_prefix}{category.lower()}_info",
                                       custom_column_type=custom_column_type_dict, custom_index=custom_index_dict))
    return sql_commands


def create_relation_table(tables_dict, comments_dict, table_prefix=config.table_prefix, custom_column_type={},
                          custom_index={}):
    # tables_dict is a dict of tables
    # comments_dict is a dict of comments
    # 'prefix' is the prefix of the database name
    # return a list of sql commands
    # FOR RELATIONS ONLY
    sql_commands = []
    for general_category in tables_dict.keys():
        # general_category -> relations_of_2_different_kinds and relations_of_a_same_kind
        for category in tables_dict[general_category].keys():
            # category -> user_user, etc.
            # database_name = f"{db_prefix}{category}"
            parties = category.split("_")
            foreign_key_names = []
            if len(parties) != len(set(parties)):
                # there are duplicate parties, add a number to the end of the party name
                for party in parties:
                    if party not in foreign_key_names:
                        foreign_key_names.append(party)
                    else:
                        foreign_key_names.append(f"{party}_{foreign_key_names.count(party)}")
            else:
                foreign_key_names = parties

            for table in tables_dict[general_category][category].keys():
                try:
                    custom_index_dict = convert_index_dict_to_attr_index_dict(custom_index[category][table])
                except KeyError:
                    custom_index_dict = {}
                table_full_name = f"{table_prefix}rel_{category.lower()}_{table.lower()}"[:64]
                table_pk = f"id"
                sql = f"CREATE TABLE {table_full_name} ({table_pk} INT NOT NULL AUTO_INCREMENT, \n"
                # add foreign keys
                for i, party in enumerate(parties):
                    sql += f"{foreign_key_names[i]}_id VARCHAR(36) NOT NULL, \n"
                for i, attribute in enumerate(tables_dict[general_category][category][table]):
                    try:
                        comment_str = re.sub(r"'", '"', comments_dict[general_category][category][table][attribute])
                    except KeyError:
                        comment_str = ""
                    if comment_str != "":
                        comment_str = f"COMMENT '{comment_str}'"
                    try:
                        custom_column_type_dict = custom_column_type[category][table]
                    except KeyError:
                        custom_column_type_dict = {}
                    sql += _generate_attr_col_sql(attribute, comment_str, custom_column_type_dict)
                sql += (f"{category.lower()}_{table.lower()}_id VARCHAR(36) UNIQUE NOT NULL, \n"
                        "create_time DATETIME DEFAULT CURRENT_TIMESTAMP, \n"
                        "create_user VARCHAR(32) DEFAULT 'system', \n"
                        "create_app VARCHAR(32) DEFAULT 'system', \n"
                        "modify_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, \n"
                        "modify_user VARCHAR(32) DEFAULT 'system', \n"
                        "modify_app VARCHAR(32) DEFAULT 'system', \n"
                        "del_stat INT DEFAULT 0, \n"
                        "version_no INT DEFAULT 0, \n"
                        f"PRIMARY KEY ({table_pk})")
                # add foreign key constraints
                for i, party in enumerate(parties):
                    sql += f", \nFOREIGN KEY ({foreign_key_names[i]}_id) REFERENCES {table_prefix}{party}_info({party}_id)"
                for attr in custom_index_dict:
                    # custom_index = {'attr': 'INDEX'}
                    sql += f", \n{custom_index_dict[attr]} ({attr})"
                sql += ");\n"
                sql_commands.append(sql)
    return sql_commands


def create_relationship_db_by_category(username, categories, prefix=config.db_prefix, user_host="localhost"):
    sql_commands = []
    for category in categories:
        sql_commands += create_db_by_category(username, categories[category], prefix=prefix, user_host=user_host)
    return sql_commands
