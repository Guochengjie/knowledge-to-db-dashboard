import re

# remove nodes higher than "level"
def prune_tree(tree, level):
    if level == 0:
        tree['children'].clear()
        # tree['value'] = 'leaf'
        return tree
    else:
        for child in tree['children']:
            prune_tree(child, level - 1)
        return tree


# now, set all nodes at max level to collapsed
def collapse_tree(tree, level):
    if level == 0:
        tree['collapsed'] = True
        return tree
    else:
        for child in tree['children']:
            collapse_tree(child, level - 1)
        return tree


def extract_children(tree):
    return tree['children']


def extract_tables(tree):
    tables_in_category = {}
    comments_in_category = {}
    # extract tables and their attributes
    """
    format:
    {'people': {'epidemicPreventionAndControlWorkers': ['type',
    'identity',
    'startTime',
    'endTime',
    'qualification']
    }
    }
    """
    for category in tree:
        tables_in_category[category['name']] = {}
        comments_in_category[category['name']] = {}
        for node in category['children']:
            tables_in_category[category['name']][node['name']] = [node['name'] for node in node['children']]
            comments_in_category[category['name']][node['name']] = {}
            for sub in node['children']:
                comments_in_category[category['name']][node['name']][sub['name']] = [leaf['name'] for leaf in
                                                                                     sub['children']]
                # now convert the comments to a string in a sorted list. Format is like:
                # 1. comment1; 2. comment2; 3. comment3
                temp_str = ""
                for i, comment in enumerate(comments_in_category[category['name']][node['name']][sub['name']]):
                    # reverse the process of camel case or snake case
                    if '_' not in comment:
                        comment = re.sub(r'([a-z])([A-Z])', r'\1 \2', comment)
                    else:
                        comment = re.sub(r'_', ' ', comment)
                    temp_str += f"{i + 1}. '{comment}'; "
                comments_in_category[category['name']][node['name']][sub['name']] = temp_str

    return tables_in_category, comments_in_category


def extract_relation_tables(tree):
    relation_dict = {}
    for relation in tree:
        relation_dict[relation['name']] = relation['children']

    tables_dict = {}
    comments_dict = {}
    for general_category in relation_dict.keys():
        tables_dict[general_category], comments_dict[general_category] = extract_tables(relation_dict[general_category])

    return tables_dict, comments_dict


def filter_entity_tree(tables, enabled_tables):
    for category in list(tables.keys()):
        if category not in list(enabled_tables.keys()):
            del tables[category]
        else:
            for table in list(tables[category].keys()):
                if table not in enabled_tables[category]:
                    del tables[category][table]


def filter_relation_tree(relations, enabled_relations):
    for relation_general_cate in list(relations.keys()):
        for relation_cate in list(relations[relation_general_cate].keys()):
            if relation_cate not in enabled_relations.keys():
                del relations[relation_general_cate][relation_cate]
            else:
                for relation in list(relations[relation_general_cate][relation_cate].keys()):
                    if relation not in enabled_relations[relation_cate]:
                        del relations[relation_general_cate][relation_cate][relation]


def filter_entity_attribute(tables, filters):
    for category in list(filters.keys()):
        for table in list(filters[category].keys()):
            list_to_remove = filters[category][table]
            original_list = tables[category][table]
            tables[category][table] = sorted(list(set(original_list) - set(list_to_remove)), key=original_list.index)


def additional_entity_attribute(tables, addtionals):
    custom_column_type = {}
    for category in list(addtionals.keys()):
        for table in list(addtionals[category].keys()):
            list_to_add = list(addtionals[category][table].keys())
            original_list = tables[category][table]
            tables[category][table] += list(set(list_to_add) - set(original_list))
            for attr in list_to_add:
                custom_column_type[attr] = addtionals[category][table][attr]
    return custom_column_type


def get_entity_table_json(tables):
    results = []
    n = 0
    for category, table in tables.items():
        for table_name, attributes in table.items():
            if table_name == "base_attributes":
                results.append(
                    {"id": n, "category": category, "table": category + "_info", "number_attribute": len(attributes),
                     "attribute": attributes})
            else:
                # otherwise, the attributes shall include those in base_attribute
                results.append({"id": n, "category": category, "table": table_name,
                                "number_attribute": len(attributes + tables[category]["base_attributes"]),
                                "attribute": attributes})
            n += 1
    return {"total": len(results), "totalNotFiltered": len(results), "rows": results}


def get_relation_table_json(relations):
    results = []
    n = 0
    for category, relation in relations.items():
        for relation_name, tables in relation.items():
            for table_name, attributes in tables.items():
                results.append({"id": n, "category": category, "relation": relation_name, "table": table_name,
                                "number_attribute": len(attributes), "attribute": attributes})
                n += 1
    return {"total": len(results), "totalNotFiltered": len(results), "rows": results}


def convert_index_dict_to_attr_index_dict(custom_index):
    if custom_index is None:
        custom_index_dict = {}
    else:
        custom_index_dict = {}
        for key in custom_index:
            for value in custom_index[key]:
                custom_index_dict[value] = key
    return custom_index_dict


def _get_attribute_json(index, attr_list, custom_attr_type_dict, comment_list, custom_index):
    results = []
    n = index
    if custom_attr_type_dict is None:
        custom_attr_type_dict = {}
    custom_index_dict = convert_index_dict_to_attr_index_dict(custom_index)
    for attr in attr_list:
        r = {"id": n, "attribute": attr, "disabled": False, "constraint": "", "comment": ""}
        if len(comment_list) != 0 and attr in comment_list.keys():
            r["comment"] = comment_list[attr]
        # check the type of the attribute
        if attr in custom_attr_type_dict.keys():
            if len(custom_attr_type_dict[attr].split(" ")) > 1:
                r["type"] = custom_attr_type_dict[attr].split(" ")[0]
                r["constraint"] = " ".join(custom_attr_type_dict[attr].split(" ")[1:])
            else:
                r["type"] = custom_attr_type_dict[attr]
        elif "date" in attr.lower():
            r["type"] = "DATE"
        elif "time" in attr.lower():
            r["type"] = "DATETIME"
        elif "place" in attr.lower() or "location" in attr.lower() or "address" in attr.lower():
            r["type"] = "VARCHAR(256)"
        else:
            r["type"] = "VARCHAR(32)"
        # check the index of the attribute
        if attr in custom_index_dict.keys():
            r["index"] = custom_index_dict[attr]
        else:
            r["index"] = ""
        n += 1
        results.append(r)
    results.append({"id": len(results), "attribute": "create_time", "disabled": True, "comment": "creation time",
                    "type": "DATETIME", "constraint": "DEFAULT CURRENT_TIMESTAMP", "index": ""})
    results.append({"id": len(results), "attribute": "create_user", "disabled": True, "comment": "creation user",
                    "type": "VARCHAR(32)", "constraint": "DEFAULT 'system'", "index": ""})
    results.append({"id": len(results), "attribute": "create_app", "disabled": True, "comment": "creation app",
                    "type": "VARCHAR(32)", "constraint": "DEFAULT 'system'", "index": ""})
    results.append(
        {"id": len(results), "attribute": "modify_time", "disabled": True, "comment": "update time", "type": "DATETIME",
         "constraint": "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", "index": ""})
    results.append({"id": len(results), "attribute": "modify_user", "disabled": True, "comment": "update user",
                    "type": "VARCHAR(32)", "constraint": "DEFAULT 'system'", "index": ""})
    results.append({"id": len(results), "attribute": "modify_app", "disabled": True, "comment": "update app",
                    "type": "VARCHAR(32)", "constraint": "DEFAULT 'system'", "index": ""})
    results.append(
        {"id": len(results), "attribute": "del_stat", "disabled": True, "comment": "delete flag", "type": "INT",
         "constraint": "DEFAULT 0", "index": ""})
    results.append(
        {"id": len(results), "attribute": "version_no", "disabled": True, "comment": "version number", "type": "INT",
         "constraint": "DEFAULT 0", "index": ""})
    return results


def get_entity_table_attribute_json(attr_list, custom_attr_type_dict={}, comment_list={}, table_name="", category="",
                                    custom_index={}):
    results = []
    if table_name[-5:] == "_info":
        results.append({"id": len(results), "attribute": "id", "disabled": True, "comment": "unique id, PRIMARY KEY",
                        "type": "INT", "constraint": "NOT NULL AUTO_INCREMENT", "index": ""})
        results.append(
            {"id": len(results), "attribute": category + "_id", "disabled": True, "comment": "UUID of the entity",
             "type": "VARCHAR(36)", "constraint": "UNIQUE NOT NULL", "index": ""})
    else:
        results.append(
            {"id": len(results), "attribute": category + "_id", "disabled": True, "comment": "unique id, FOREIGN KEY",
             "type": "INT", "constraint": "UNIQUE NOT NULL", "index": ""})
    results += _get_attribute_json(len(results), attr_list, custom_attr_type_dict, comment_list, custom_index)

    return {"total": len(results), "totalNotFiltered": len(results), "rows": results}


def get_relation_table_attribute_json(attr_list, custom_attr_type_dict={}, comment_list={}, table_name="", category="",
                                      custom_index={}):
    results = [{"id": 0, "attribute": "id", "disabled": True, "comment": "unique id, PRIMARY KEY", "type": "INT",
                "constraint": "NOT NULL AUTO_INCREMENT", "index": ""}]
    # split the category (like user_region) into two parts (user and region)
    category_list = category.split("_")
    for party in category_list:
        results.append(
            {"id": len(results), "attribute": party + "_id", "disabled": True, "comment": "UUID, FOREIGN KEY",
             "type": "VARCHAR(36)", "constraint": "NOT NULL", "index": ""})
    results.append({"id": len(results), "attribute": f"{category}_{table_name}_id", "disabled": True,
                    "comment": "UUID of relation", "type": "VARCHAR(36)", "constraint": "UNIQUE NOT NULL", "index": ""})
    results += _get_attribute_json(len(results), attr_list, custom_attr_type_dict, comment_list, custom_index)
    return {"total": len(results), "totalNotFiltered": len(results), "rows": results}
