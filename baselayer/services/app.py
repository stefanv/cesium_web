import importlib

from zmq.eventloop import ioloop
ioloop.install()

from baselayer.app import cfg
from baselayer.app.app_server import handlers, settings
app_factory = cfg['app:factory']

module, app_factory = app_factory.rsplit('.', 1)
app_factory = getattr(importlib.import_module(module), app_factory)

import tornado.log
app = app_factory(debug=True)
app._baselayer_cfg = cfg
app.cfg = cfg

app.listen(cfg['app:port'])

ioloop.IOLoop.current().start()
