from apps import db


# class Task is a model that defines a task and related user (using foreign key)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))
    db_username = db.Column(db.String(30))
    db_password = db.Column(db.String(30))
    db_host = db.Column(db.String(30))
    db_name = db.Column(db.String(30))
    table_prefix = db.Column(db.String(10))
    custom_attr_type = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    del_flag = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Task %r>' % self.id

    def __init__(self, title, description, task_uuid, user_id):
        self.uuid = task_uuid
        self.description = description
        self.title = title
        self.user_id = user_id
