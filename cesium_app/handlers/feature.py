from .base import BaseHandler, AccessError
from ..models import Dataset, Featureset, Project, File
from ..config import cfg

from os.path import join as pjoin
import uuid


# XXX TODO XXX This will no longer be necessary
def featurize_and_notify(username, fset_id, ts_paths, features_to_use,
                         fset_path, custom_features_script=None):
    import requests

    payload = {'type': 'featurize',
               'params': {'ts_paths': ts_paths,
                          'features_to_use': features_to_use,
                          'output_path': fset_path},
               'metadata': {'fset_id': fset_id, 'username': username}}
    result = requests.post('http://127.0.0.1:63000/task',
                           json=payload).json()
    if result['status'] == 'success':
        return result['data']['task_id']
    else:
        raise RuntimeError("Featurization failed: {}".format(result['message']))


class FeatureHandler(BaseHandler):
    def _get_featureset(self, featureset_id):
        try:
            f = Featureset.get(Featureset.id == featureset_id)
        except Featureset.DoesNotExist:
            raise AccessError('No such featureset')

        if not f.is_owned_by(self.get_username()):
            raise AccessError('No such feautreset')

        return f


    def get(self, featureset_id=None):
        if featureset_id is not None:
            f = self._get_featureset(featureset_id)
        else:
            featureset_info = [f for p in Project.all(self.get_username())
                               for f in p.featuresets]

        self.success(featureset_info)


    def post(self):
        data = self.get_json()
        featureset_name = data.get('featuresetName', '')
        dataset_id = int(data['datasetID'])
        feature_fields = {feature: selected for (feature, selected) in
                          data.items() if feature.startswith(('sci_', 'obs_',
                                                              'lmb_'))}
        feat_type_name = [feat.split('_', 1) for (feat, selected) in
                          feature_fields.items() if selected]
        features_to_use = [fname for (ftype, fname) in feat_type_name]

        custom_feats_code = data['customFeatsCode'].strip()

        fset_path = pjoin(cfg['paths']['features_folder'],
                          '{}_featureset.nc'.format(uuid.uuid4()))

        dataset = Dataset.get(Dataset.id == dataset_id)

        fset = Featureset.create(name=featureset_name,
                                 file=File.create(uri=fset_path),
                                 project=dataset.project,
                                 features_list=features_to_use,
                                 custom_features_script=None)
        res = featurize_and_notify(self.get_username(), fset.id, dataset.uris,
                                   features_to_use, fset_path,
                                   custom_features_script=None).apply_async()
        fset.task_id = res.task_id
        fset.save()

        self.success(fset, 'cesium/FETCH_FEATURESETS')

    def delete(self, featureset_id):
        f = self._get_featureset(featureset_id)
        f.delete_instance()

        self.success(action='cesium/FETCH_FEATURESETS')

    def put(self, featureset_id):
        f = self._get_featureset(featureset_id)
        self.error("Functionality for this endpoint is not yet implemented.")
