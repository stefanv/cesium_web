import peewee as pw
from playhouse.shortcuts import model_to_dict
from .json_util import to_json


# The db has to be initialized later; this is done by the app itself
# See `app_server.py`
db = pw.PostgresqlDatabase(None, autocommit=True, autorollback=True)


class BaseModel(signals.Model):
    """All other models are derived from this one.

    It adds the following:

    - __dict__ method to convert the model to a dict
    - __str__ method to convert the model to a JSON string: `str(my_model)`
    - Specify the database in use

    """
    def __str__(self):
        return to_json(self.__dict__())

    def __dict__(self):
        return model_to_dict(self, recurse=False, backrefs=False)

    class Meta:
        database = db
