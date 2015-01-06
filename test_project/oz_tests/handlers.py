"""Defines application handlers"""

import oz
import tornado.web
from .models import *
from oz import aws_cdn, bandit, blinks, json_api, redis, redis_sessions, sqlalchemy, error_pages

class FileHandler(oz.RequestHandler, redis.RedisMiddleware, aws_cdn.CDNMiddleware):
    def get(self, path):
        # Gets the contents of a file
        f = self.get_file(path)

        if not f.exists():
            raise tornado.web.HTTPError(404)

        self.finish(f.contents())

    def put(self, path):
        # Sets the contents of a file to the request body
        replace = self.get_argument("replace") == "true"
        self.upload_file(path, self.request.body, replace=replace)

    def delete(self, path):
        # Deletes a file
        try:
            self.remove_file(path)
        except:
            raise tornado.web.HTTPError(404)

class FileCopyingHandler(oz.RequestHandler, redis.RedisMiddleware, aws_cdn.CDNMiddleware):
    def put(self, from_path, to_path):
        # Copies a file from one path to another
        replace = self.get_argument("replace") == "true"
        self.copy_file(from_path, to_path, replace=replace)

class CacheBusterHandler(oz.RequestHandler, redis.RedisMiddleware, aws_cdn.CDNMiddleware):
    def get(self, path):
        # Gets a cache buster value
        buster = self.get_cache_buster(path)

        if buster == None:
            raise tornado.web.HTTPError(404)

        self.finish(buster)

    def put(self, path):
        # Sets a cache buster value
        self.set_cache_buster(path, self.get_argument("hash"))

    def delete(self, path):
        # Removes a cahce buster value
        self.remove_cache_buster(path)

class ExperimentHandler(oz.RequestHandler, redis.RedisMiddleware, redis_sessions.RedisSessionMiddleware, bandit.BanditTestingMiddleware):
    def get(self, name):
        # Gets the choice for a given experiment
        choice = self.get_experiment_choice(name)

        if choice == None:
            raise tornado.web.HTTPError(404)

        self.finish(choice)

    def post(self, name):
        # Sets a choice for a given experiment using the bandit algorithm
        exp = bandit.Experiment(self.redis(), name)
        exp.add()
        exp.add_choice("A")
        exp.add_choice("B")
        exp.add_choice("C")

        self.choose_experiment(name)

    def put(self, name):
        # Explicitly sets a choice for a given experiment
        self.join_experiment(name, self.get_argument("choice"))

    def delete(self, name):
        # Removes the currently set choice for an experiment
        self.leave_experiment(name)

        # Delete the experiment
        for key in self.redis().keys("bandit:*:v2"):
            self.redis().delete(key)

class BlinkHandler(oz.RequestHandler, blinks.BlinkMiddleware):
    def get(self):
        # Gets a blink value
        self.finish("%s:%s" % self.get_blink())

    def put(self):
        # Sets a blink balue
        self.set_blink(self.get_argument("value"), self.get_argument("type"))

class EchoApiHandler(oz.RequestHandler, json_api.ApiMiddleware):
    def post(self):
        # Echoes the JSON body
        self.respond(self.body())

class NormalErrorApiHandler(oz.RequestHandler, json_api.ApiMiddleware):
    def get(self):
        # Raises an API error
        raise json_api.ApiError("uhoh")

class UnexpectedErrorApiHandler(oz.RequestHandler, json_api.ApiMiddleware):
    def get(self):
        # Raises a non-API erorr
        raise Exception("uhoh")

class SessionHandler(oz.RequestHandler, redis.RedisMiddleware, redis_sessions.RedisSessionMiddleware):
    def delete(self):
        # Deletes all session values
        self.clear_all_session_values()

class SessionValueHandler(oz.RequestHandler, redis.RedisMiddleware, redis_sessions.RedisSessionMiddleware):
    def get(self, key):
        # Gets a session value
        self.finish(self.get_session_value(key))

    def put(self, key):
        # Sets a session value
        self.set_session_value(key, self.get_argument("value"))

    def delete(self, key):
        # Deletes a session value
        self.clear_session_value(key)

class DatabaseHandler(oz.RequestHandler, sqlalchemy.SQLAlchemyMiddleware):
    def get(self, key):
        # Gest an option value
        value = self.db().query(Option).filter(Option.key == key).first()

        if value == None:
            raise tornado.web.HTTPError(404)

        self.finish(value.value)

    def put(self, key):
        # Sets an option value
        value = self.db().query(Option).filter(Option.key == key).first()

        if value == None:
            value = Option(key=key)

        value.value = self.get_argument("value")
        self.db().add(value)

class HtmlErrorHandler(oz.RequestHandler, error_pages.ErrorPageMiddleware):
    def get(self):
        raise Exception("Uhoh")
