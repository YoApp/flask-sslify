# -*- coding: utf-8 -*-

from flask import request, redirect, current_app

YEAR_IN_SECS = 31536000


class SSLify(object):
    """Secures your Flask App."""

    excluded_endpoints = None

    def __init__(self, app=None, age=YEAR_IN_SECS, subdomains=False, permanent=False):
        self.excluded_endpoints = []
        self.hsts_age = age
        self.hsts_include_subdomains = subdomains
        self.permanent = permanent

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Configures the configured Flask app to enforce SSL."""

        app.before_request(self.redirect_to_ssl)
        app.after_request(self.set_hsts_header)

    def exclude_endpoint(self, fn):
        """Excludes an endpoint."""
        self.excluded_endpoints.append(fn)
        return fn

    @property
    def hsts_header(self):
        """Returns the proper HSTS policy."""
        hsts_policy = 'max-age={0}'.format(self.hsts_age)

        if self.hsts_include_subdomains:
            hsts_policy += '; includeSubDomains'

        return hsts_policy

    def redirect_to_ssl(self):
        """Redirect incoming requests to HTTPS."""
        # Should we redirect?
        criteria = [
            request.is_secure,
            current_app.debug,
            request.headers.get('X-Forwarded-Proto', 'http') == 'https',
            current_app.view_functions.get(request.endpoint) in \
                self.excluded_endpoints
        ]

        enabled = current_app.config.get('SSLIFY_ENABLED')
        if not any(criteria) and enabled:
            if request.url.startswith('http://'):
                url = request.url.replace('http://', 'https://', 1)
                code = 302
                if self.permanent:
                    code = 301
                r = redirect(url, code=code)

                return r

    def set_hsts_header(self, response):
        """Adds HSTS header to each response."""
        if request.is_secure:
            response.headers.setdefault('Strict-Transport-Security', self.hsts_header)
        return response
