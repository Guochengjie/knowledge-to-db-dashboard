from urban_knowledge import *
import inspect
import sys

# Configurations
MYSQL_USER = 'knowledge_db'
MYSQL_PASSWORD = 'a5HLxMxPrdbN4CRC'
MYSQL_HOST = 'dev.guoch.xyz'
MYSQL_PORT = '3306'
MYSQL_DB = 'knowledge_db'

# CROS Configurations
allow_origins = [
    "*"
]

api_route_prefix = "/api/v1"

allow_methods=["*"]
allow_headers=["*"]

# FastAPI Metadata
title = "Urban Knowledge RESTful Server"
description = "A RESTful API for Urban Knowledge, generated automatically by a Python script from the Knowledge System for Intelligent Cities."
contact = {
    "name": "Chengjie Guo",
    "email": "i@guoch.xyz",
    "url": "https://guoch.xyz",
}


def change_case(str):
    return ''.join(['_'+i.lower() if i.isupper()
               else i for i in str]).lstrip('_')


module = sys.modules['urban_knowledge']

classes_list = []

for cls_name, cls in inspect.getmembers(module, inspect.isclass):
    if cls.__module__ == 'urban_knowledge':
        classes_list.append(cls_name)

fast_api_template = """
{class_name}Model = sqlalchemy_to_pydantic({class_name})

# Add a new resource
# the primary key will be generated automatically, so the given primary key will be ignored
@app.post("{api_route_prefix}/{class_name_lower}/add", tags=["{class_name_lower}"])
async def {class_name_lower}_add(commons: dict = Depends({class_name}Model)):
    new_item = {class_name}()
    results_dict = dict(commons)
    for key, value in results_dict.items():
        # Skip the primary key
        if key == list(results_dict.keys())[0]:
            continue
        setattr(new_item, key, value)
    if not new_item.uuid:
        new_item.uuid = re.sub("-","", str(uuid.uuid4()))
    else:
        new_item.uuid = re.sub("-","", new_item.uuid)
    session.add(new_item)
    session.commit()
    return {{'data': dict({class_name}Model.from_orm(new_item)), "message": "Success", "code": 200}}

# Get the resource based on the fields given
# Resources will by filtered by all the given fields
# If del_stat not is not given, it will be set to 0 by default
@app.get("{api_route_prefix}/{class_name_lower}/get", tags=["{class_name_lower}"])
async def {class_name_lower}_get(commons: dict = Depends({class_name}Model)):
    results_dict = dict(commons)
    if not results_dict['del_stat']:
        results_dict['del_stat'] = 0

    for key in list(results_dict.keys()):
        if not results_dict[key]:
            results_dict.pop(key)
    return {{'data': jsonable_encoder(session.query({class_name}).filter_by(**results_dict).all()), "message": "OK", "code": 200}}

# Edit the resource based on the primary key
# If the primary key is not given, an error will be returned
# If the resource has been deleted, an error will be returned
# If the resource has not been deleted, the resource will be updated with all the given fields
@app.post("{api_route_prefix}/{class_name_lower}/edit", tags=["{class_name_lower}"])
async def {class_name_lower}_edit(commons: dict = Depends({class_name}Model)):
    results_dict = dict(commons)
    if not results_dict[list(results_dict.keys())[0]]:
        return {{'data': None, "message": "Primary Key must be given", "code": 401}}
    if results_dict['del_stat'] != 0:
        return {{'data': None, "message": "The resource has been removed", "code": 401}}
    else:
        item = session.query({class_name}).get(results_dict[list(results_dict.keys())[0]])
        for key, value in results_dict.items():
            if value:
                setattr(item, key, value)
        session.commit()
        return {{'data': dict({class_name}Model.from_orm(item)), "message": "Success", "code": 200}}

# Delete the resource based on the primary key
# the resource will not be deleted from the database, but the del_stat will be set to 1
@app.get("{api_route_prefix}/{class_name_lower}/delete", tags=["{class_name_lower}"])
async def {class_name_lower}_delete(commons: dict = Depends({class_name}Model)):
    results_dict = dict(commons)
    if not results_dict[list(results_dict.keys())[0]]:
        return {{'data': None, "message": "Primary Key must be given", "code": 401}}
    else:
        item = session.query({class_name}).get(results_dict[list(results_dict.keys())[0]])
        item.del_stat = 1
        session.commit()
        return {{'data': dict({class_name}Model.from_orm(item)), "message": "Success", "code": 200}}
"""

fast_api_output = f"""
import fastapi
from fastapi import Depends, FastAPI
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urban_knowledge import *
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import uuid
import re


MYSQL_USER = '{MYSQL_USER}'
MYSQL_PASSWORD = '{MYSQL_PASSWORD}'
MYSQL_HOST = '{MYSQL_HOST}'
MYSQL_PORT = '{MYSQL_PORT}'
MYSQL_DB = '{MYSQL_DB}'
""" 

fast_api_output += """
# create the engine
engine = create_engine(f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}', echo=True)
# create the session
Session = sessionmaker(bind=engine)
session = Session()
"""

fast_api_output += f"""
app = fastapi.FastAPI(title="{title}", discription="{description}", contact={contact})

app.add_middleware(
    CORSMiddleware,
    allow_origins={allow_origins},
    allow_credentials=True,
    allow_methods={allow_methods},
    allow_headers={allow_headers},
)
"""

for class_name in classes_list:
    fast_api_output += fast_api_template.format(class_name_lower=change_case(class_name), class_name=class_name, api_route_prefix=api_route_prefix)

fast_api_output += """
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

with open("fastapi_server.py", "w") as f:
    f.write(fast_api_output)
