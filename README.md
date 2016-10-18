# Oz [![Build Status](https://travis-ci.org/dailymuse/oz.png)](https://travis-ci.org/dailymuse/oz) #

Oz is a framework that provides sensible defaults, scaffolding and boilerplate
for [tornado](https://github.com/facebook/tornado)-based projects.

Oz applications are composed entirely of plugins that allow you to easily
share and re-use logic across sites.

Requires tornado >= 3.1.

## Getting Started ##

First, install oz:

    pip install oz

Then create a new project:

    oz init <project name>

Compose your project's plugin, then run the tests:

    oz test

Then run the application server:

    oz server

Alternatively, you can get started using
[oz-bootstrap](https://github.com/ysimonson/oz-bootstrap), which provides a more rapid
means of getting off the ground.

## Project Structure ##

Once you've created a new project, you'll have a directory structure like so:

* \<project name\>/ - contains the plugin for your project
  * \_\_init\_\_.py - specifies what sub-modules to import on plugin load
  * handlers.py - by convention, this specifies application request handlers
  * models.py - by convention, this specifies models for the application
  * options.py - by convention, this specifies application-specific options
  * routes.py - by convention, this specifies application routes, which maps
    URL patterns to request handlers
* static/ - static assets that can be served by tornado's static asset engine
* templates/ - tornado templates
* config.py - specifies the application configuration, including what plugins to load

## Plugins ##

Oz apps are composed entirely of plugins - including the logic specific to
your application. This makes the execution model straight-forward, and makes it
easy to refactor a project to abstract out generic logic.

Plugins expose actions, middleware, routes, options and UIModules to extend
app functionality. You can mix and match plugins in any way - an application's
config.py specifies a list of plugins to load. At application load time, these
plugins are loaded in-order.

## Actions ##

When you run oz, the first argument specifies what action - or callback - to
run. These actions will have access to the full application context.

Oz's core plugin (loaded by default, but it can be replaced) provides a few
actions:

* `init` - starts a new project
* `server` - starts the oz server
* `repl` - starts an IPython REPL instance, with the application context
  available
* `test` - runs unit tests

Plugins can specify their own actions to add new functionality. To add a new
action, wrap a function in your plugin with the `@oz.action` decorator. e.g.

    @oz.action
    def hello(name):
        print "Hello, %s!" % name

This creates a new action that will say hello. To run it, execute
`oz hello Jose`, which will print `Hello, Jose!` and quit.

## Request Handlers and Routes ##

An oz `RequestHandler` extend vanilla `RequestHandler`s to allow for
middleware. If you want to take advantage of middleware, make sure to inherit
from this rather than the default tornado request handler. You add middleware
to a request handler through multiple inheritance.

Request handlers are made available by specifying a route via `oz.route`, which
takes a single route specification, or `oz.routes`, which takes many.

An example handler using API middleware:

    class ExampleApiHandler(oz.RequestHandler, oz.json_api.ApiMiddleware):
        def get(self):
            self.respond({"foo": "bar"})

    oz.route(("/", ExampleApiHandler))

## Middleware ##

Middleware provide a mechanism for extending functionality at the
request handler level. You can fire off logic when specific events occur, and
provide additional methods that are exposed on the request handler and in
templates.

There's nothing magical about middleware - in fact middleware classes tend to
inherit straight from Python's built-in `object`. Here's an example:

    class FooMiddleware(object):
        def __init__(self):
            print "FooMiddleware initialized"
            super(FooMiddleware, self).__init__()

        def combine_arguments(self, baz):
            foo = self.get_argument("foo")
            bar = self.get_argument("bar")
            return "%s : %s : %s" % (foo, bar, baz)

Request handlers can then attach this middleware by inheriting from it:

    class FooHandler(oz.RequestHandler, FooMiddleware):
        def get(self):
            self.render_template("foo.html", value=self.combine_arguments("c"))

Due to multiple inheritance, the `FooHandler` now has access to all of the
methods in `FooMiddleware`, including `combine_arguments`.

*Note that when a middleware class overrides `__init__`, to, e.g. add template
helpers, it must call super's `__init__`. Otherwise the inheritance chain
could be broken, and not all middleware functionality may work.*

### Template Helpers ###

A template helper is a middleware method exposed to templates. You can add a
new template helper by calling `template_helper`, e.g.:

    class FooMiddleware(object):
        def __init__(self):
            super(FooMiddleware, self).__init__()

            # Add the template helper
            self.template_helper("combine_arguments", self.combine_arguments)

        def combine_arguments(self, baz):
            foo = self.get_argument("foo")
            bar = self.get_argument("bar")
            return "%s : %s : %s" % (foo, bar, baz)

The method `combine_arguments` will then be available in templates. You could
use it in a template as such:

    {{ combine_arguments("c") }}

If the query/POST parameters foo='a' and bar='b' for the request, then this
will print `a : b : c`.

### Triggers ###

Middleware and request handlers can hook into a number of events to trigger
custom logic. When a trigger fires, the oz request handler will call all of
the functions that have registered to be associated with the given trigger
name, in order, unless one of them returns `oz.break_trigger` (in which case
the trigger will bail.)

You can fire a trigger from a request handler or middleware like so:

    self.trigger("event name", *args, **kwargs)

This will call all the functions associated with the trigger called
`event name`. You can register a new function to be associated like so:

    self.trigger_listener("event name", self.some_method)

The oz request handler has a number of triggers it fires automatically:

* `initialize` - called when the request handler is setup.
* `prepare` - made before the relevant HTTP verb method is called.
* `on_finish` - made after a request has completed.
* `on_connection_close` - called when an HTTP connection is closed.
* `write_error` - Called when an error needs to be written.

You can register against any of these to pick up the event. For example, let's
say we wanted to provide a middleware that exposes a per-request database
transaction. You could do the following implementation:

    class DatabaseConnectionMiddleware(object):
        def __init__(self):
            super(DatabaseConnectionMiddleware, self).__init__()
            self.trigger_listener("prepare", self._on_database_prepare)
            self.trigger_listener("on_finish", self._on_database_finish)

        def db(self):
            return self.transaction

        def _on_database_prepare(self):
            self.transaction = create_database_transaction()

        def _on_database_finish(self):
            if self.handler.get_status() >= 200 and self.handler.get_status() < 399:
                self.transaction.commit()
            else:
                self.transaction.rollback()
                return oz.break_trigger

This will create a new connection before an HTTP verb method is called, and
either commit or rollback the transaction after the request completes,
depending on the status code. Request handlers would be able to access the
transaction by calling `self.db()`.

## Options ##

You can force application options to be present and correctly typed for use in
your plugin. These options (specified in `app_options` of `config.py`) are
checked at application initialization time. Specify one option with
`oz.option`, or many with `oz.options`. e.g.

    oz.option("allow_jsonp", type=bool, default=True, help="Whether to allow for JSONP requests")

Example using oz.options:

    oz.options(
        aws_access_key = dict(type=str, help="AWS access key for CDN"),
        aws_secret_key = dict(type=str, help="AWS secret key for CDN"),
        static_host = dict(type=str, help="CDN hostname for static assets"),
        s3_bucket = dict(type=str, default=None, help="S3 bucket for uploading CDN assets")
    )

## UIModules ##

You can expose
[tornado UIModules](http://www.tornadoweb.org/en/branch2.2/web.html#tornado.web.UIModule)
by using the `@oz.uimodule` decorator. e.g.

    @oz.uimodule
    class HelloModule(tornado.web.UIModule):
        def render(self, name):
            print "Hello, %s!" % name

The UIModule will automatically be available in tornado templates. e.g. within
a tornado template, you could call `HelloModule` like so:

    {% module HelloModule("Jose") %}

Which will print `Hello, Jose!` in the template.

## Built-In Plugins ##

Oz comes with a number of built-in plugins to faciliate rapid development.

### Core (`oz.core`) ###

This should be included in every project, unless you really want to modify the
default actions or options. The core plugin includes three actions: one for
running the application server (`server`), one for starting a repl with access
to the application context (`repl`), and one for running the unit tests
(`test`).

### AWS CDN (`oz.aws_cdn`) ###

This plugin uses AWS infrastructure to serve static assets. Static assets are
hosted on S3 and served with a far-future expiration time. Cache busters are
used to ensure old cached assets are never served and to maximize performance.
This plugin also lets you customize the static host so that you can put a CDN
in front of the S3 host.

When an S3 bucket is not specified in the app options, the plugin defaults to
manipulating static assets on the local filesystem that are served with
tornado's static asset engine. This is useful for local development
environments.

Requires the redis plugin, as cache buster values are stored in the redis
database. Also requires boto.

This plugin adds a new action, called `cache_busting_scan`. This will forcibly
re-compute the cache buster values for files with the specified prefixes.
e.g.:

    oz cache_busting_scan somefile.txt path/to/otherfiles/

This command will re-compute the cache busters for somefile.txt and all files
in path/to/otherfiles/.

A number of utility functions for S3 and cache buster manipulation are
provided in the plugin (`oz.aws_cdn`). A middleware
(`oz.aws_cdn.CDNMiddleware`) provides shortcuts to these functions
through request handler helpers, by using the application options.

### Bandit (`oz.bandit`) ###

Adds
[bandit testing](http://untyped.com/untyping/2011/02/11/stop-ab-testing-and-make-out-like-a-bandit/)
functionality to a site, which are similar to A/B tests.

### Blinks (`oz.blinks`) ###

Provides a middleware (`oz.blinks.BlinkMiddleware`) for getting and
setting blinks, which are one-time transactional messages displayed on a
per-session basis. You can use these to, e.g. give a "you have logged out"
message to users.

### Pretty error pages (`oz.error_pages`) ###

Pretty Django-like error pages that are displayed when the server is in debug
mode. Make sure to copy `oz/error_pages/error_page.html` to your
templates directory and specify its path via the `error_pages_template`
option.

### JSON API (`oz.json_api`) ###

Provides a middleware (`oz.json_api.ApiMiddleware`) that can be applied
on API-based request handlers that speak JSON(P). API-based request handlers can
raise `oz.json_api.ApiError` to provide standardized JSON(P) error
messages.

### Redis (`oz.redis`) ###

Provides a middleware (`oz.redis.RedisMiddleware`) that will provide a
redis connection as a request handler helper.

### Redis Sessions (`oz.redis_sessions`) ###

Provides user sessions that are tied to a redis connection. Requires the redis
middleware. Session manipulation functionality is exposed through request
handler helpers on the middleware
(`oz.redis_sessions.RedisSessionMiddleware`).

### SQLAlchemy (`oz.sqlalchemy`) ###

Adds SQLAlchemy support, with per-request database transactions (SQLAlchemy
sessions). Transactions will be committed if a request handler returns a
status code between 200 and 399, and rollback otherwise. You can access the
SQLAlchemy session via `self.db()` once the middleware is attached
(`oz.sqlalchemy.SQLAlchemyMiddleware`).
