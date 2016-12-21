"""
Tool provider for LTI requests
"""
import logging
from lti import ToolProvider
from oauthlib.oauth1.rfc5849.endpoints import BaseEndpoint
from oauthlib.oauth1.rfc5849 import errors

LOG = logging.getLogger(__name__)

class CWToolProvider(ToolProvider):
    '''
    Tool provider for LTI requests
    '''

    @classmethod
    def from_flask_request(cls, secret=None, request=None):
        '''
        Convert Flask request into the proper LTI object
        '''
        if request is None:
            raise ValueError('This will not work without a request')

        params = request.form.copy()
        headers = dict(request.headers)
        url = request.url
        return cls.from_unpacked_request(secret, params, url, headers)

    def is_valid_request(self, validator):
        """
        Is the request a valid OAuth1 request?
        """
        valid = False
        endpoint = BaseEndpoint(validator)
        # Fake HTTPS in the URL because our F5 load balancer gives us HTTP
        request = endpoint._create_request(
            'https' + self.launch_url[4:],
            'POST',
            self.to_params(),
            self.launch_headers
            )
        request.client_key = request.oauth_consumer_key
        request.signature = request.oauth_signature
        request.signature_method = request.oauth_signature_method
        request.timestamp = request.oauth_timestamp
        request.nonce = request.oauth_nonce

        try:
            endpoint._check_mandatory_parameters(request)
        except errors.OAuth1Error as err:
            LOG.error("[Failure!] %s", err.description)
            return False

        if not validator.validate_timestamp_and_nonce(
            request.oauth_consumer_key,
            request.oauth_timestamp,
            request.oauth_nonce,
            request
            ):
            LOG.error("[Failure!] Invalid timestamp or nonce")
            return False

        valid_client = validator.validate_client_key(
            request.oauth_consumer_key,
            request
            )
        # Create a new request with clean parameters
        request = endpoint._create_request(
            'https' + self.launch_url[4:],
            'POST',
            self.to_params(),
            self.launch_headers
            )
        if not valid_client:
            request.oauth_consumer_key = validator.dummy_client

        valid_signature = endpoint._check_signature(request)

        valid = all((valid_client, valid_signature))
        if not valid:
            LOG.error("[Failure!] request verification failed.")
            LOG.error("  Valid client: %s", valid_client)
            LOG.error("  Valid signature: %s", valid_signature)

        return valid
