"""API specification using Open API"""

import flask
import apispec
from apispec.ext.marshmallow.swagger import FIELD_MAPPING

from .plugin import CONVERTER_MAPPING


PLUGINS = (
    'flask_rest_api.spec.plugin',
    # XXX: Ideally, we shouldn't register schema_path_helper but it's
    # hard to extract only what we want from apispec.ext.marshmallow
    'apispec.ext.marshmallow',
)


class APISpec(apispec.APISpec):
    """API specification class

    :param Flask app: Flask application
    """

    def __init__(self, app=None):
        # We need to pass title and version as they are positional parameters
        # Those values are replaced in init_app
        super().__init__(title='OpenAPI spec', version='1', plugins=PLUGINS)
        self._app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize ApiSpec with application"""

        self._app = app

        # API info from app
        self.info['title'] = app.name
        self.info['version'] = app.config.get('API_VERSION', '1')

        # Add routes to json spec file and spec UI (ReDoc)
        api_url = app.config.get('OPENAPI_URL_PREFIX', None)
        if api_url:
            blueprint = flask.Blueprint(
                'api-docs',
                __name__,
                url_prefix=api_url,
                template_folder='./templates',
            )
            # Serve json spec at 'url_prefix/api-docs.json' by default
            json_url = app.config.get('OPENAPI_JSON_PATH', 'api-docs.json')
            blueprint.add_url_rule(
                json_url, view_func=self.openapi_json)
            # Serve ReDoc only if path specified
            redoc_url = app.config.get('OPENAPI_REDOC_PATH', None)
            if redoc_url:
                blueprint.add_url_rule(
                    redoc_url, view_func=self.openapi_redoc)
            app.register_blueprint(blueprint)

    def openapi_json(self):
        """Serve JSON spec file"""
        return flask.jsonify(self.to_dict())

    def openapi_redoc(self):
        """Expose OpenAPI spec with ReDoc

        The Redoc script URL can be specified using OPENAPI_REDOC_URL.
        By default, a CDN script is used. When using a CDN script, the
        version can (and should) be specified using OPENAPI_REDOC_VERSION,
        otherwise, 'latest' is used.
        OPENAPI_REDOC_VERSION is ignored when OPENAPI_REDOC_URL is passed.
        """
        redoc_url = self._app.config.get('OPENAPI_REDOC_URL', None)
        if redoc_url is None:
            redoc_version = self._app.config.get(
                'OPENAPI_REDOC_VERSION', 'latest')
            redoc_url = ('https://rebilly.github.io/ReDoc/releases/'
                         '{}/redoc.min.js'.format(redoc_version))
        return flask.render_template(
            'redoc.html', title=self._app.name, redoc_url=redoc_url)

    def register_converter(self, converter, conv_type, conv_format):
        CONVERTER_MAPPING[converter] = (conv_type, conv_format)

    def register_field(self, field, field_type, field_format):
        FIELD_MAPPING[field] = (field_type, field_format)

    def register_spec_plugin(self, plugin):
        self.setup_plugin(plugin)
