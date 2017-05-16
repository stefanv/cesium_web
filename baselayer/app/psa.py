"""
Python Social Auth: storage and user model definitions

https://github.com/python-social-auth
"""

from social_sqlalchemy.storage import (
     BaseStorage,
    AssociationMixin, CodeMixin,
    NonceMixin, PartialMixin, UserMixin
)

from social_core.backends.google import GoogleOAuth2

from sqlalchemy.orm import relationship
from .models import Base, User#, db


#database_proxy.initialize(db)  # TODO initialize


class UserSocialAuth(Base, UserMixin):
    """
    This model is used by PSA to store whatever it needs during
    authentication, e.g. token expiration time, etc.
    """
    user = relationship('User', back_populates='social_auth')

    @classmethod
    def user_model(cls):
        return User


class TornadoStorage(BaseStorage):
    """
    Storage definition for Tornado.

    We use PSA's default implementation.

    http://python-social-auth.readthedocs.io/en/latest/storage.html#storage-interface
    """

    class nonce(NonceMixin):
        """Single use numbers"""
        pass

    class association(AssociationMixin):
        """OpenId account association"""
        pass

    class code(CodeMixin):
        """Mail validation single one time use code"""
        pass

    class partial(PartialMixin):
        pass

    user = UserSocialAuth


class FakeGoogleOAuth2(GoogleOAuth2):
    AUTHORIZATION_URL = 'http://localhost:63000/fakeoauth2/auth'
    ACCESS_TOKEN_URL = 'http://localhost:63000/fakeoauth2/token'

    def user_data(self, access_token, *args, **kwargs):
        return {
            'id': 'testuser@gmail.com',
            'emails': [{'value': 'testuser@gmail.com', 'type': 'home'}]
        }
