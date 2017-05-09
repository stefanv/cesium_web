import os
import pathlib

from .config import Config


def load_config(config_files=None):
    if config_files is None:
        basedir = pathlib.Path(os.path.dirname(__file__))/'..'
        config_files = (basedir/'baselayer.yaml.example', basedir/'baselayer.yaml')
        config_files = (c.absolute() for c in config_files)

    cfg = Config(config_files)

    return cfg
