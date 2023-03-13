from knowledge2db import config, tree_utilities, translator
from knowledge2db.tree_utilities import prune_tree, collapse_tree
import xml.etree.ElementTree as ET
import re

if config.translate:
    if config.translator == "youdao":
        from knowledge2db.translator import youdao_translate as translator
    elif config.translator == "caiyun":
        from knowledge2db.translator import caiyun_translate as translator


def opml_loader(filename: str):
    # Load the OPML file
    # Return the root of the tree if the file is standard OPML file
    try:
        tree = ET.parse(filename)
    except FileNotFoundError:
        print("File not found")
        return None

    root = tree.getroot()
    if root.find("body"):
        if root.find("body").find("outline"):
            return root.find("body").find("outline")
    print("The input file is not standard OPML file")
    return None


def elementtree_to_dicttree(tree: ET, type="entity", translate=True, naming=config.naming):
    # convert the element tree to a dictionary tree
    # the dictionary tree can be used by echarts directly
    if type not in ["entity", "relation"]:
        print("type must be entity or relation")
        raise ValueError("type must be entity or relation")

    translation_source_set = set()

    # iterate the tree, call itself until the leaf node, return a list of nodes
    def tree_iterator(t: ET):
        if '_note' in t.attrib.keys():
            translation_source_set.add(t.attrib['text'])
            # translation_source_set.add(t.attrib['_note'])
            node_dict = {"name": t.attrib['text'], 'children': []}
            # node_dict = {"name": t.attrib['text'], 'note': t.attrib['_note'], 'value': "node", 'children': []}
        else:
            translation_source_set.add(t.attrib['text'])
            node_dict = {"name": t.attrib['text'], 'children': []}
            # node_dict = {"name": t.attrib['text'], 'note': "", 'value': "node", 'children': []}
        for child in t:
            node_dict['children'].append(tree_iterator(child))
        return node_dict

    # get a tree from the ET
    # results are in its original language
    t = tree_iterator(tree)
    # t["value"] = "root"
    if config.debug:
        print("translation_source_set:", translation_source_set)

    # translate the tree
    if translate:
        translation_source_list = list(translation_source_set)
        translation_result_list = translator(translation_source_list, naming)
        translation_dict = dict(zip(translation_source_list, translation_result_list))
        translation_dict[""] = ""

        def translate_tree(t):
            t["name"] = translation_dict[t["name"]]
            # t["note"] = translation_dict[t["note"]]
            for child in t["children"]:
                translate_tree(child)

        translate_tree(t)

    if type == "entity":
        prune_tree(t, 4)
        collapse_tree(t, 2)

    elif type == "relation":
        prune_tree(t, 5)
        collapse_tree(t, 3)
    return t


def loader(filename: str, type="entity"):
    if type not in ["entity", "relation"]:
        raise ValueError("type must be entity or relation")
    tree = opml_loader(filename)
    if config.debug:
        print("tree:", tree)
    if tree:
        return elementtree_to_dicttree(tree, type, config.translate)
    else:
        return None
