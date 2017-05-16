import datetime
import os
import sys
import inspect
import time
import pandas as pd

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.orm.exc import NoResultFound

from baselayer.app.json_util import to_json
from baselayer.app.handlers.base import AccessError

from cesium import featurize


# The db has to be initialized later; this is done by the app itself
# See `app_server.py`
def connect(user, password, db, host='localhost', port=5432):
    '''Returns a connection'''
    # We connect with the help of the PostgreSQL URL
    # postgresql://federer:grandestslam@localhost:5432/tennis
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user, password, host, port, db)

    # The return value of create_engine() is our connection object
    conn = sa.create_engine(url, client_encoding='utf8')

    return conn


# TODO where does this info live? it's not part of the connection anymore
from types import SimpleNamespace; db = SimpleNamespace(database='cesium')
# TODO don't auto-connect
conn = connect('cesium', '', 'cesium')
DBSession = scoped_session(sessionmaker(conn))
session = DBSession()
from sqlalchemy.exc import ProgrammingError
for table in ['dataset', 'featureset', 'file', 'model', 'project', 'prediction', 'user']:
    try:
        conn.execute(f'ALTER TABLE "{table}" RENAME TO {table}s')
    except ProgrammingError as e:
        if "does not exist" not in str(e):
            raise
try:
    conn.execute('ALTER TABLE datasetfile RENAME TO dataset_files')
except ProgrammingError as e:
    if "does not exist" not in str(e):
        raise
try:
    conn.execute('ALTER TABLE userproject RENAME TO user_projects')
except ProgrammingError as e:
    if "does not exist" not in str(e):
        raise

class BaseMixin(object):
    query = DBSession.query_property()
    id = sa.Column(sa.Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + 's'

    def __str__(self):
        return to_json(self)

    def is_owned_by(self, user):
        if hasattr(self, 'users'):
            return (user in self.users)
        elif hasattr(self, 'project'):
            return (user in self.project.users)
        else:
            raise NotImplementedError(f"{type(self)} object has no owner")

    @classmethod
    def get_if_owned_by(cls, ident, user):
        try:
            obj = cls.query.get(ident)
        except NoResultFound:
            raise AccessError('No such feature set')

        if not obj.is_owned_by(user):
            raise AccessError('No such feature set')

        return obj


Base = declarative_base(cls=BaseMixin)
Base.metadata.bind = conn


dataset_files = sa.Table('dataset_files', Base.metadata,
    sa.Column('dataset_id', sa.ForeignKey('datasets.id', ondelete='CASCADE'),
              primary_key=True),
    sa.Column('file_uri', sa.ForeignKey('files.uri', ondelete='CASCADE'),
              primary_key=True))


user_projects = sa.Table('user_projects', Base.metadata,
    sa.Column('user_id', sa.ForeignKey('users.id', ondelete='CASCADE'),
              primary_key=True),
    sa.Column('project_id', sa.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True))


class Dataset(Base):
    name = sa.Column(sa.String(), nullable=False)
    created = sa.Column(sa.DateTime, nullable=False,
                        default=datetime.datetime.now)
    meta_features = sa.Column(sa.ARRAY(sa.VARCHAR()), nullable=False,
                              default=[], index=True)
    project_id = sa.Column(sa.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    project = relationship('Project')
    files = relationship('File', secondary=dataset_files,
                         back_populates='datasets')

    def display_info(self):
        info = self.__dict__()
        info['files'] = [os.path.basename(fname)
                         for fname in self.file_names]

        return info


class Project(Base):
    name = sa.Column(sa.String(), nullable=False)
    description = sa.Column(sa.String())
    created = sa.Column(sa.DateTime, nullable=False,
                        default=datetime.datetime.now)
    users = relationship('User', secondary=user_projects,
                         back_populates='projects')


# TODO: remove files on database delete
class File(Base):
    id = None  # no ID field
    uri = sa.Column(sa.String(), primary_key=True)
    name = sa.Column(sa.String())
    created = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now)
    datasets = relationship('Dataset', secondary=dataset_files,
                            back_populates='files')


class Featureset(Base):
    project_id = sa.Column(sa.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    name = sa.Column(sa.String(), nullable=False)
    created = sa.Column(sa.DateTime, nullable=False, default=datetime.datetime.now)
    features_list = sa.Column(sa.ARRAY(sa.VARCHAR()), nullable=False, index=True)
    custom_features_script = sa.Column(sa.String())
    file_uri = sa.Column(sa.ForeignKey('files.uri', ondelete='CASCADE'),
                        nullable=False, index=True)
    task_id = sa.Column(sa.String())
    finished = sa.Column(sa.DateTime)

    file = relationship('File')
    project = relationship('Project')


class Model(Base):
    project_id = sa.Column(sa.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    featureset_id = sa.Column(sa.ForeignKey('featuresets.id',
                                            ondelete='CASCADE'),
                              nullable=False, index=True)
    name = sa.Column(sa.String(), nullable=False)
    created = sa.Column(sa.DateTime, nullable=False,
                        default=datetime.datetime.now)
    params = sa.Column(sa.JSON, nullable=False, index=False)
    type = sa.Column(sa.String(), nullable=False)
    file_uri = sa.Column(sa.ForeignKey('files.uri', ondelete='CASCADE'),
                        nullable=False, index=True)
    task_id = sa.Column(sa.String())
    finished = sa.Column(sa.DateTime)
    train_score = sa.Column(sa.Float)

    featureset = relationship('Featureset')
    file = relationship('File')
    project = relationship('Project')


class Prediction(Base):
    project_id = sa.Column(sa.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    dataset_id = sa.Column(sa.ForeignKey('datasets.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    model_id = sa.Column(sa.ForeignKey('models.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    created = sa.Column(sa.DateTime, nullable=False,
                        default=datetime.datetime.now)
    file_uri = sa.Column(sa.ForeignKey('files.uri', ondelete='CASCADE'),
                        nullable=False, index=True)
    task_id = sa.Column(sa.String())
    finished = sa.Column(sa.DateTime)

    dataset = relationship('Dataset')
    file = relationship('File')
    model = relationship('Model')
    project = relationship('Project')

    def format_pred_data(fset, data):
        fset.columns = fset.columns.droplevel('channel')
        fset.index = fset.index.astype(str)  # can't use ints as sa.JSON keys

        labels = pd.Series(data['labels'] if len(data.get('labels', [])) > 0
                           else None, index=fset.index)

        if len(data.get('pred_probs', [])) > 0:
            preds = pd.DataFrame(data.get('pred_probs', []),
                                 index=fset.index).to_dict(orient='index')
        else:
            preds = pd.Series(data['preds'], index=fset.index).to_dict()
        result = {name: {'features': feats, 'label': labels.loc[name],
                         'prediction': preds[name]}
                  for name, feats in fset.to_dict(orient='index').items()}
        return result

    def display_info(self):
        info = self.__dict__()
        info['model_type'] = self.model.type
        info['dataset_name'] = self.dataset.name
        info['model_name'] = self.model.name
        info['featureset_name'] = self.model.featureset.name
        if self.task_id is None:
            fset, data = featurize.load_featureset(self.files.uri)
            info['isProbabilistic'] = (len(data['pred_probs']) > 0)
            info['results'] = Prediction.format_pred_data(fset, data)
        return info


class User(Base):
    username = sa.Column(sa.String(), nullable=False, unique=True)
    email = sa.Column(sa.String(), nullable=False, unique=True)
    projects = relationship('Project', secondary=user_projects,
                            back_populates='users')

    @classmethod
    def user_model(cls):
        return User

    def is_authenticated(self):
        return True

    def is_active(self):
        return True
