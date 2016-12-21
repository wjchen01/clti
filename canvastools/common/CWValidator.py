'''
Validator class for OAuth1
'''
from oauthlib.oauth1 import RequestValidator
from ..common import auth

class CWValidator(RequestValidator):
    """
    Validator class for OAuth1
    """

    @property
    def timestamp_lifetime(self):
        return 900

    @property
    def nonce_length(self):
        return 20, 50

    def validate_timestamp_and_nonce(self,
                                     key, timestamp, nonce, request,
                                     request_token=None,
                                     access_token=None):
        '''
        Save timestamp and nonce to database and ensure that they are unique
        '''
        params = {
            'timestamp': timestamp,
            'nonce': nonce
            }
        return not auth.seentsn(params)

    def validate_client_key(self, key, request):
        '''
        Check request key against key from local config
        '''
        return auth.oauth_consumer_key(request) == key

    def dummy_client(self):
        """
        Return dummy client key to foil hacking attempts based on timing
        """
        return 'dummyfoo'

    def get_client_secret(self, key, request):
        """
        Retrieve secret from local config
        """
        return auth.oauth_consumer_secret(request)

    def dummy_request_token(self):
        '''
        Not implemented in Courseworks
        '''
        return ''

    def dummy_access_token(self):
        '''
        Not implemented in Courseworks
        '''
        return ''

    def get_request_token_secret(self, key, token, request):
        '''
        Not implemented in Courseworks
        '''
        return ""

    def get_access_token_secret(self, key, token, request):
        '''
        Not implemented in Courseworks
        '''
        return ""
