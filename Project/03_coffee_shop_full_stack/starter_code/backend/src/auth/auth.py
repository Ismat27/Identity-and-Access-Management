import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'coffee-tenant.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'http://127.0.0.1:5000'

# AuthError Exception


class AuthError(Exception):
    '''
        AuthError Exception
        A standardized way to communicate auth failure modes
    '''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

def get_token_auth_header():
    """To obtain the Access Token from the Authorization Header
    """
    authorization_header = request.headers.get('Authorization', None)
    if not authorization_header:
        raise AuthError({
            'code': 'authorization_header_is_not_included',
            'description': 'Authorization header must be included'
        }, 401)
    parts = authorization_header.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_authorization_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) <= 1:
        raise AuthError({
            'code': 'invalid_authorization_header',
            'description': 'Token not found or not included.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_authorization_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    authorization_token = parts[1]
    return authorization_token


def check_permissions(permission, payload):
    """To authorize user by its permissions
    """
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True


def verify_decode_jwt(token):
    """To verify JWT gotten from authorization header
    """
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description':
                'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
                payload = verify_decode_jwt(token)
            except Exception as e:
                abort(401)
            check_permissions(permission, payload)
            return func(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
