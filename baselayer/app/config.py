import yaml
import os
import pathlib
import glob


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


def load_config(config_files=None):
    basedir = pathlib.Path(os.path.dirname(__file__))/'..'
    baselayer_config_files = [basedir/'baselayer.yaml.example',
                              basedir/'baselayer.yaml']
    baselayer_config_files = [os.path.abspath(c.absolute()) for c in
                              baselayer_config_files]

    parent_app_config_files = glob.glob('*.yaml*')

    config_files = (baselayer_config_files + parent_app_config_files +
                    ([os.path.abspath(c) for c in config_files] if config_files
                     is not None else []))

    cfg = Config(config_files)

    return cfg


if __name__ == "__main__":
    show()
