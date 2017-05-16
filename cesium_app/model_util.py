import inspect
import textwrap
import time
from contextlib import contextmanager

from cesium_app import models#, psa
from cesium_app.json_util import to_json


@contextmanager
def status(message):
    print(f'[·] {message}', end='')
    try:
        yield
    except:
        print(f'\r[✗] {message}')
        raise
    else:
        print(f'\r[✓] {message}')


# TODO connect to db
def drop_tables():
    print(f'Dropping tables on database "{models.db.database}"')
    models.Base.metadata.drop_all()


def create_tables(retry=5):
    """
    Create tables for all models, retrying 5 times at intervals of 3
    seconds if the database is not reachable.
    """
    for i in range(1, retry + 1):
        try:
            print(f'Refreshing tables on db "{models.db.database}"')
            models.Base.metadata.create_all()

            print('Refreshed tables:')
            for m in models.Base.metadata.tables:
                print(f' - {m}')

            return

        except Exception as e:
            if (i == retry):
                raise e
            else:
                print('Could not connect to database...sleeping 3')
                time.sleep(3)


def clear_tables():
    drop_tables()
    create_tables()


def insert_test_data():
    with status("Dropping all tables"):
        drop_tables()

    with status("Creating tables"):
        create_tables()

    for model in models.Base.metadata.tables:
        print('    -', model)

    USERNAME = 'testuser@gmail.com'
    with status(f"Creating dummy user: {USERNAME}... "):
        u = models.User(username=USERNAME, email=USERNAME)
        models.DBSession().add(u)
        models.DBSession().commit()

    for i in range(3):
        with status("Inserting dummy project"):
            p = models.Project(name=f'test project {i}', users=[u])
            models.DBSession().add(p)
            models.DBSession().commit()

        print(f"\n{textwrap.indent(str(p), '  ')}\n")

    with status("Assert that user has 3 projects"):
        assert len(u.projects) == 3

    with status("Inserting dummy dataset and time series... "):
        files = [models.File(uri=f'/dir/ts{i}.npz') for i in range(3)]
        d = models.Dataset(name='test dataset', project=p, files=files)
        models.DBSession().add_all(files + [d])
        models.DBSession().commit()

    with status("Inserting dummy featureset... "):
        test_file = models.File.query[0]
        f = models.Featureset(project=p, name='test featureset',
                              file=test_file, features_list=['amplitude'])
        models.DBSession().add(f)
        models.DBSession().commit()

    with status("Inserting dummy model... "):
        m = models.Model(project=p, featureset=f, name='test model',
                         params={'n_estimators': 10}, type='RFC',
                         file=test_file)
        models.DBSession().add(m)
        models.DBSession().commit()

    with status("Inserting dummy prediction... "):
        pr = models.Prediction(project=p, model=m, file=test_file, dataset=d)
        models.DBSession().add(pr)
        models.DBSession().commit()


if __name__ == "__main__":
    insert_test_data()
