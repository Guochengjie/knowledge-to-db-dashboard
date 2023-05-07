from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.widgets import CheckboxInput, ListWidget


# form to add or edit a task
# which has a title, a description and 2 opml files
class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()],
                        render_kw={"placeholder": "Title", "class": "form-control", "type": "text"})
    description = TextAreaField('Description', validators=[DataRequired()],
                                render_kw={"class": "form-control", "placeholder": "Description"})
    entity_opml_file = FileField('Entity OPML File',
                                 validators=[FileRequired(), FileAllowed(['opml'], 'OPML files only!')],
                                 render_kw={"class": "form-control"})
    relation_opml_file = FileField('Relation OPML File',
                                   validators=[FileRequired(), FileAllowed(['opml'], 'OPML files only!')],
                                   render_kw={"class": "form-control"})
    table_prefix = StringField('Table Prefix', validators=[DataRequired()],
                               render_kw={"placeholder": "Table Prefix", "class": "form-control", "type": "text"},
                               default="t_")


# a form to collect necessary information to build a java package
# needed information:
# db_engine, db_port (int), db_host, db_username, db_password, db_name -> input
# relation -> single choice
# attribute needed when joining tables -> multiple choice
class JavaRelationPackageFrom(FlaskForm):
    db_engine = SelectField('Database Engine', choices=[('mysql', 'MySQL'), ('postgresql', 'PostgreSQL')],
                            validators=[DataRequired()], render_kw={"class": "form-select"})
    db_port = StringField('Database Port', validators=[DataRequired()],
                          render_kw={"placeholder": "Database Port", "class": "form-control", "type": "number"})
    db_host = StringField('Database Host', validators=[DataRequired()],
                          render_kw={"placeholder": "Database Host", "class": "form-control", "type": "text"})
    db_username = StringField('Database Username', validators=[DataRequired()],
                              render_kw={"placeholder": "Database Username", "class": "form-control", "type": "text"})
    db_password = StringField('Database Password', validators=[DataRequired()],
                              render_kw={"placeholder": "Database Password", "class": "form-control",
                                         "type": "password"})
    db_name = StringField('Database Name', validators=[DataRequired()],
                          render_kw={"placeholder": "Database Name", "class": "form-control", "type": "text"})
    relation = SelectField('Relation', coerce=str, choices=[],
                           render_kw={"class": "form-select"}, validate_choice=False)
    attributes = StringField('Attributes', validators=[DataRequired()], render_kw={"class": "form-control", "type": "text"})
