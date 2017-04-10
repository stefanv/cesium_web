from .base import BaseHandler

import tornado.web


class ProfileHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        return self.success({'username': self.current_user})


class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie('user_id')
        self.redirect('/')
