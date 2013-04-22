#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""Utility library for reading user information from an id_token.

This is an experimental library that can temporarily be used to extract
a user from an id_token.  The functionality provided by this library
will be provided elsewhere in the future.

_set_oauth_user_vars monkey patched by Gerwin Sturm to temporarily fix
an issue with mixed case email addresses
"""

import logging
import os
from google.appengine.api import oauth

_ENV_AUTH_EMAIL = 'ENDPOINTS_AUTH_EMAIL'
_ENV_AUTH_DOMAIN = 'ENDPOINTS_AUTH_DOMAIN'
_ENV_USE_OAUTH_SCOPE = 'ENDPOINTS_USE_OAUTH_SCOPE'


def _set_oauth_user_vars(token_info, audiences, allowed_client_ids, scopes,
                         local_dev):
    """Validate the oauth token and set endpoints auth user variables.

    If the oauth token is valid, this sets either the ENDPOINTS_AUTH_EMAIL and
    ENDPOINTS_AUTH_DOMAIN environment variables (in local development) or
    the ENDPOINTS_USE_OAUTH_SCOPE one.  These provide enough information
    that our endpoints.get_current_user() function can get the user.

    Args:
      token_info: Info returned about the oauth token from the tokeninfo endpoint.
      audiences: List of audiences that are acceptable, or None for first-party.
      allowed_client_ids: List of client IDs that are acceptable.
      scopes: List of acceptable scopes.
      local_dev: True if we're running a local dev server, false if we're in prod.
    """
    if 'email' not in token_info:
        logging.warning('Oauth token doesn\'t include an email address.')
        return
    if not token_info.get('verified_email'):
        logging.warning('Oauth token email isn\'t verified.')
        return

    if audiences or allowed_client_ids:
        if 'audience' not in token_info:
            logging.warning('Audience is required and isn\'t specified in token.')
            return

        if token_info['audience'] in audiences:
            pass
        elif (token_info['audience'] == token_info.get('issued_to') and
              allowed_client_ids is not None and
              token_info['audience'] in allowed_client_ids):
            pass
        else:
            logging.warning('Oauth token audience isn\'t permitted.')
            return

    token_scopes = token_info.get('scope', '').split(' ')
    if not any(scope in scopes for scope in token_scopes):
        logging.warning('Oauth token scopes don\'t match any acceptable scopes.')
        return

    if local_dev:
        os.environ[_ENV_AUTH_EMAIL] = token_info['email']
        os.environ[_ENV_AUTH_DOMAIN] = ''
        return

    for scope in scopes:
        try:
            oauth_user = oauth.get_current_user(scope)
            oauth_scope = scope
            break
        except oauth.Error:
            pass
    else:
        logging.warning('Oauth framework couldn\'t find a user.')
        return None

    """
    Original: if oauth_user.email() == token_info['email']:

    Email addresses are case-insensitive and this caused a problem
    for people who signed up with mixed-case email addresses
    because token_info["email"] was lower case while oauth_user.email()
    had the mixed case.
    Temporary fix for monkey patching until the issue is resolved in the
    google.appengine.ext.endpoints.users_id_token or google.appengine.api.oauth
    """
    if oauth_user.email().lower() == token_info['email'].lower():
        os.environ[_ENV_USE_OAUTH_SCOPE] = oauth_scope
        return

    logging.warning('Oauth framework user didn\'t match oauth token user.')
    return None


# Monkey patching...
from google.appengine.ext.endpoints import users_id_token
users_id_token._set_oauth_user_vars = _set_oauth_user_vars
