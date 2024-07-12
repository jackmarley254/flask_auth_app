from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

user_organization = db.Table(
    'user_organization',
    db.Column('user_id', db.String, db.ForeignKey('user.userId'),
              primary_key=True),
    db.Column('organization_id', db.String, db.ForeignKey
              ('organization.orgId'), primary_key=True)
)


class User(db.Model):
    userId = db.Column(db.String, primary_key=True,
                       default=lambda: str(uuid.uuid4()),
                       unique=True, nullable=False)
    firstName = db.Column(db.String, nullable=False)
    lastName = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    phone = db.Column(db.String)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Organization(db.Model):
    orgId = db.Column(db.String, primary_key=True,
                      default=lambda: str(uuid.uuid4()), unique=True,
                      nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

    users = db.relationship('User', secondary=user_organization,
                            backref=db.backref('organizations',
                                               lazy='dynamic'))
