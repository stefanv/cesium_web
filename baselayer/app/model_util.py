import inspect
import textwrap
import time
import peewee as pw
from contextlib import contextmanager

from . import models
from . import psa
from .json_util import to_json


@contextmanager
def status(message):
    print('[·] {}'.format(message), end='')
    try:
        yield
    except:
        print('\r[✗] {}'.format(message))
        raise
    else:
        print('\r[✓] {}'.format(message))


def _filter_pw_models(members):
    return [obj for (name, obj) in members
                if inspect.isclass(obj) and issubclass(obj, pw.Model)
                and not obj == models.BaseModel]


app_models = _filter_pw_models(inspect.getmembers(models))
psa_models = _filter_pw_models(inspect.getmembers(psa))
all_models = app_models + psa_models


def drop_tables():
    print('Dropping tables on database "{}"'.format(models.db.database))
    models.db.drop_tables(all_models, safe=True, cascade=True)


def create_tables(retry=5):
    """
    Create tables for all models, retrying 5 times at intervals of 3
    seconds if the database is not reachable.
    """
    for i in range(1, retry + 1):
        try:
            print('Refreshing tables on db "{}"'.format(models.db.database))
            models.db.create_tables(all_models, safe=True)

            print('Refreshed tables:')
            for m in all_models:
                print(' - {}'.format(m.__name__))

            return

        except Exception as e:
            if (i == retry):
                raise e
            else:
                print('Could not connect to database...sleeping 5')
                time.sleep(3)


def clear_tables():
    drop_tables()
    create_tables()
