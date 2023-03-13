from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed


# form to add or edit a task
# which has a title, a description and 2 opml files
class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()], render_kw={"placeholder": "Title", "class": "form-control", "type": "text"})
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": "Description"})
    entity_opml_file = FileField('Entity OPML File', validators=[FileRequired(), FileAllowed(['opml'], 'OPML files only!')], render_kw={"class": "form-control"})
    relation_opml_file = FileField('Relation OPML File', validators=[FileRequired(), FileAllowed(['opml'], 'OPML files only!')], render_kw={"class": "form-control"})
