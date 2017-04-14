import tornado.web

from .config import cfg

import sys

# This provides `login`, `complete`, and `disconnect` endpoints
from social_tornado.routes import SOCIAL_AUTH_ROUTES

from .handlers import (
    MainPageHandler,
    ProjectHandler,
    DatasetHandler,
    FeatureHandler,
    ModelHandler,
    PredictionHandler,
    FeatureListHandler,
    SklearnModelsHandler,
    SocketAuthTokenHandler,
    PlotFeaturesHandler,
    PredictRawDataHandler,
    ProfileHandler,
    LogoutHandler
)


def make_app():
    """Create and return a `tornado.web.Application` object with specified
    handlers and settings.
    """
    settings = {
        'template_path': './static',
        'autoreload': '--debug' in sys.argv,
        'cookie_secret': cfg['app']['secret-key'],
        'login_url': '/',

        # Python Social Auth configuration
        'SOCIAL_AUTH_USER_MODEL': 'cesium_app.models.User',
        'SOCIAL_AUTH_STORAGE': 'cesium_app.psa.TornadoPeeweeStorage',
        'SOCIAL_AUTH_STRATEGY': 'social_tornado.strategy.TornadoStrategy',
        'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': (
            'social_core.backends.google.GoogleOAuth2',
        ),
        'SOCIAL_AUTH_LOGIN_URL': '/',
        'SOCIAL_AUTH_LOGIN_REDIRECT_URL': '/',  # on success
        'SOCIAL_AUTH_LOGIN_ERROR_URL': '/login-error/',

        'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL': True,

        'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY':
            cfg['server']['auth']['google_oauth2_key'],
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': \
            cfg['server']['auth']['google_oauth2_secret'],
    }

    if settings['cookie_secret'] == 'abc01234':
        print('!' * 80)
        print('  Your server is insecure. Please update the secret string ')
        print('  in the configuration file!')
        print('!' * 80)

    handlers = SOCIAL_AUTH_ROUTES + [
        (r'/project(/.*)?', ProjectHandler),
        (r'/dataset(/.*)?', DatasetHandler),
        (r'/features(/.*)?', FeatureHandler),
        (r'/models(/.*)?', ModelHandler),
        (r'/predictions(/[0-9]+)?', PredictionHandler),
        (r'/predictions/([0-9]+)/(download)', PredictionHandler),
        (r'/predict_raw_data', PredictRawDataHandler),
        (r'/features_list', FeatureListHandler),
        (r'/socket_auth_token', SocketAuthTokenHandler),
        (r'/sklearn_models', SklearnModelsHandler),
        (r'/plot_features/(.*)', PlotFeaturesHandler),
        (r'/profile', ProfileHandler),
        (r'/logout', LogoutHandler),

        (r'/()', MainPageHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static/'}),
        (r'/(favicon.png)', tornado.web.StaticFileHandler, {'path': 'static/'})
    ]

    if cfg['server']['auth']['debug_login']:
        settings['SOCIAL_AUTH_AUTHENTICATION_BACKENDS'] = (
            'cesium_app.psa.FakeGoogleOAuth2',
        )

    app = tornado.web.Application(handlers, **settings)
    app.cfg = cfg

    return app
