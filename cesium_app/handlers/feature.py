import tornado.ioloop

import xarray as xr
from cesium import featurize, time_series

from .base import BaseHandler, AccessError
from ..models import Dataset, Featureset, Project, File
from ..config import cfg

from os.path import join as pjoin
import uuid


def featurize_task(executor, ts_paths, features_to_use, output_path,
                   custom_script_path=None):
    all_time_series = executor.map(time_series.from_netcdf, ts_paths)
    all_features = executor.map(featurize.featurize_single_ts, all_time_series,
                                features_to_use=features_to_use,
                                custom_script_path=custom_script_path)
    fset = executor.submit(featurize.assemble_featureset, all_features,
                           all_time_series)
    return executor.submit(xr.Dataset.to_netcdf, fset, output_path)


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


    @tornado.gen.coroutine
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
        custom_script_path = None

        fset_path = pjoin(cfg['paths']['features_folder'],
                          '{}_featureset.nc'.format(uuid.uuid4()))

        dataset = Dataset.get(Dataset.id == dataset_id)

        fset = Featureset.create(name=featureset_name,
                                 file=File.create(uri=fset_path),
                                 project=dataset.project,
                                 features_list=features_to_use,
                                 custom_features_script=None)

        loop = tornado.ioloop.IOLoop.current()

        from distributed import Scheduler
        IP = '127.0.0.1'
        PORT = 63000
        PORT_SCHEDULER = 63500
        from distributed import Executor
        executor = Executor('{}:{}'.format(IP, PORT_SCHEDULER), loop=loop,
                            start=False)
        loop.add_future(executor._start(), None)

        s = Scheduler(loop=loop)
        s.start(PORT_SCHEDULER)
        print('Task scheduler listening on port {}'.format(PORT_SCHEDULER))

        from distributed import Worker
        w = Worker('127.0.0.1', PORT_SCHEDULER, loop=loop)
        w.start(0)
        print('Single worker activated')
        loop.start()

        future = featurize_task(executor, dataset.uris, features_to_use,
                                fset_path, custom_script_path)
        loop.spawn_callback(report_result, future, task_data['metadata'])

        fset.task_id = future.key
        fset.save()

        self.success(fset, 'cesium/FETCH_FEATURESETS')

    def delete(self, featureset_id):
        f = self._get_featureset(featureset_id)
        f.delete_instance()

        self.success(action='cesium/FETCH_FEATURESETS')

    def put(self, featureset_id):
        f = self._get_featureset(featureset_id)
        self.error("Functionality for this endpoint is not yet implemented.")
