import os
import tempfile

from cesium_app import models as m
from cesium_app.tests.fixtures import project, dataset


# TODO
def test_dataset_delete(project, dataset):
    """Test that deleting a `Dataset` also removes any associated files."""
    uris = [f.uri for f in dataset.files]
    assert all(os.path.exists(f) for f in uris)
    m.DBSession().delete(dataset)
    m.DBSession().commit()
    assert not any(os.path.exists(f) for f in uris)
