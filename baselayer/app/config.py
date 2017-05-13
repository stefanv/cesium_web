import yaml
import os
import pathlib


class Config(dict):
    def __init__(self, config_files=None):
        dict.__init__(self)
        if config_files is not None:
            for f in config_files:
                self.update_from(f)

    def update_from(self, filename):
        """Update configuration from YAML file"""
        if os.path.isfile(filename):
            more_cfg = yaml.load(open(filename))
            dict.update(self, more_cfg)
            print('[baselayer] Loaded {}'.format(os.path.relpath(filename)))

    def __getitem__(self, key):
        keys = key.split(':')

        val = self
        for key in keys:
            val = val.get(key)
            if val is None:
                return None

        return val

    def show(self):
        """Print configuration"""
        print()
        print("=" * 78)
        print("Configuration")

        for key in self:
            print("-" * 78)
            print(key)

            if isinstance(self[key], dict):
                for key, val in self[key].items():
                    print('  ', key.ljust(30), val)

        print("=" * 78)


def load_baselayer_config(config_files=None):
    if config_files is None:
        basedir = pathlib.Path(os.path.dirname(__file__))/'..'
        config_files = (basedir/'baselayer.yaml.example', basedir/'baselayer.yaml')
        config_files = (c.absolute() for c in config_files)

    cfg = Config(config_files)

    return cfg


if __name__ == "__main__":
    show()
