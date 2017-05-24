'''Assortment of fixtures for use in test modules.'''

import uuid
import os
from os.path import join as pjoin
from cesium_app.models import (DBSession, User, Project, DatasetFile, Dataset,
                               Featureset, Model, Prediction)
from cesium import data_management, featurize
from cesium.tests.fixtures import sample_featureset
from cesium.features import CADENCE_FEATS, GENERAL_FEATS, LOMB_SCARGLE_FEATS
from cesium_app.ext.sklearn_models import MODELS_TYPE_DICT
import shutil
import datetime
import joblib
import pandas as pd

#from .conftest import cfg
import pytest
from sqlalchemy.orm.exc import ObjectDeletedError, StaleDataError
import factory


class ProjectFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = DBSession()
        sqlalchemy_session_persistence = 'commit'
        model = Project
    name = 'test_proj'
    description = 'test_desc'
    users = []

    @factory.post_generation
    def set_user(project, create, extracted, **kwargs):
        if not create:
            return

        # TODO what if user doesn't exist yet?
        project.name += f' {project.id}'  # TODO testing
        project.users = User.query.filter(User.username ==
                                          'testuser@gmail.com').all()
        DBSession().commit()


class DatasetFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = DBSession()
        sqlalchemy_session_persistence = 'commit'
        model = Dataset
    name = 'test_ds'
    project = factory.SubFactory(ProjectFactory)

    @factory.post_generation
    def add_files(dataset, create, label_type='class', *args, **kwargs):
        if not create:
            return

        if label_type == 'class':
            header = pjoin(os.path.dirname(__file__),
                           'data', 'asas_training_subset_classes.dat')
        elif label_type == 'regr':
            header = pjoin(os.path.dirname(__file__),
                           'data', 'asas_training_subset_targets.dat')
        else:
            header = None
        tarball = pjoin(os.path.dirname(__file__),
                        'data', 'asas_training_subset.tar.gz')
        # TODO can we use a tmpdir or not?
        header = shutil.copy2(header, '/tmp') if header else None
        tarball = shutil.copy2(tarball, '/tmp')
        ts_paths = data_management.parse_and_store_ts_data(
            tarball, '/tmp', header)
        
        dataset.files = [DatasetFile(uri=uri) for uri in ts_paths]
        DBSession().commit()


class FeaturesetFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = DBSession()
        sqlalchemy_session_persistence = 'commit'
        model = Featureset
    project = factory.SubFactory(ProjectFactory)
    name = 'class',
    features_list = (CADENCE_FEATS + GENERAL_FEATS + LOMB_SCARGLE_FEATS)
    finished = datetime.datetime.now()

    @factory.post_generation
    def add_file(featureset, create, value, *args, **kwargs):
        if not create:
            return

        if 'class' in featureset.name:
            labels = ['Mira', 'Classical_Cepheid']
        elif 'regr' in featureset.name:
            labels = [2.2, 3.4, 4.4, 2.2, 3.1]
        else:
            labels = []
        fset_data, fset_labels = sample_featureset(5, 1,
                                                   featureset.features_list,
                                                   labels)
        fset_path = pjoin('/tmp', '{}.npz'.format(str(uuid.uuid4())))
        featurize.save_featureset(fset_data, fset_path, labels=fset_labels)
        featureset.file_uri = fset_path
        featureset.name += f' {featureset.id}'  # TODO testing
        DBSession().commit()


class ModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = DBSession()
        sqlalchemy_session_persistence = 'commit'
        model = Model
    project = factory.SubFactory(ProjectFactory)
    name = 'test_model'
    featureset = factory.SubFactory(FeaturesetFactory)
    type = 'RandomForestClassifier'
    params = {}
    finished = datetime.datetime.now()

    @factory.post_generation
    def add_file(model, create, value, *args, **kwargs):
        model_params = {
            "RandomForestClassifier": {
                "bootstrap": True, "criterion": "gini",
                "oob_score": False, "max_features": "auto",
                "n_estimators": 10, "random_state": 0},
            "RandomForestRegressor": {
                "bootstrap": True, "criterion": "mse",
                "oob_score": False, "max_features": "auto",
                "n_estimators": 10},
            "LinearSGDClassifier": {
                "loss": "hinge"},
            "LinearRegressor": {
                "fit_intercept": True}}
        fset_data, data = featurize.load_featureset(model.featureset.file_uri)
        model_data = MODELS_TYPE_DICT[model.type](**model_params[model.type])
        model_data.fit(fset_data, data['labels'])
        model.file_uri = pjoin('/tmp/', '{}.pkl'.format(str(uuid.uuid4())))
        joblib.dump(model, model.file_uri)
        DBSession().commit()


'''
@pytest.fixture(scope='function')
def prediction(dataset, model, featureset):
    """Create and yield test prediction, then delete.

    Params
    ------
    dataset : `models.Dataset` instance
        Dummy dataset used to create prediction instance.
    model : `models.Model` instance
        The model to use to create prediction.
    featureset : `models.Featureset` instance, optional
        The featureset on which prediction will be performed. If None,
        the featureset associated with `model` will be used. Defaults
        to None.
    """
    fset, data = featurize.load_featureset(featureset.file_uri)
    model_data = joblib.load(model.file_uri)
    if hasattr(model_data, 'best_estimator_'):
        model_data = model_data.best_estimator_
    preds = model_data.predict(fset)
    pred_probs = (pd.DataFrame(model_data.predict_proba(fset),
                               index=fset.index, columns=model_data.classes_)
                  if hasattr(model_data, 'predict_proba') else [])
    all_classes = model_data.classes_ if hasattr(model_data, 'classes_') else []
    pred_path = pjoin(cfg['paths:predictions_folder'],
                      '{}.npz'.format(str(uuid.uuid4())))
    featurize.save_featureset(fset, pred_path, labels=data['labels'],
                              preds=preds, pred_probs=pred_probs)
    pred = Prediction(file_uri=pred_path, dataset=dataset,
                      project=dataset.project, model=model,
                      finished=datetime.datetime.now())
    DBSession().add(pred)
    DBSession().commit()

    try:
        yield pred
        DBSession().delete(pred)
        DBSession().commit()
    except (ObjectDeletedError, StaleDataError): 
        DBSession().rollback()
'''
