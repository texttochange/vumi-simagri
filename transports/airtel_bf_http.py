import sys
from urllib import urlencode

from twisted.internet.defer import inlineCallbacks
from twisted.web.resource import Resource
from twisted.web import http

from vumi.transports.base import Transport
from vumi.utils import http_request_full
from vumi.errors import MissingMessageField
from vumi.log import log


class AirtelBfHttpTransport(Transport):
    
    mandatory_inbound_message_fields = []
    
    @inlineCallbacks
    def setup_transport(self):
        log.msg("Setup yo transport %s" % self.config)
        self.web_resource = yield self.start_web_resources(
            [
                (AirtelBfHttpReceiveSMSResource(self), self.config['receive_path'])
                ],
            self.config['receive_port'])

    def get_transport_url(self, suffix=''):
        addr = self.web_resource.getHost()
        return "http://%s:%s/%s" % (addr.host, addr.port, suffix.lstrip('/'))

    @inlineCallbacks
    def teardown_transport(self):
        yield self.web_resource.loseConnection()

    @inlineCallbacks
    def handle_outbound_message(self, message):
        log.msg("Outbound message to be processed %s" % repr(message))
        try:
            params = {
                'DA': message['from_addr'],
                'SOA': message['to_addr'],
                'content': (message['content'] or '').encode("utf8"),
                'u': self.config['login'],
                'p': self.config['password']}
            encoded_params = urlencode(params)
            log.msg('Hitting %s with %s' % (self.config['outbound_url'], encoded_params))
            response = yield http_request_full(
                "%s?%s" % (self.config['outbound_url'], encoded_params),
                method='GET')
            log.msg("Response: (%s) %r" % (response.code, response.delivered_body))
            content = response.delivered_body.strip()            
            
            if response.code == 200:
                yield self.publish_ack(
                    user_message_id=message['message_id'],
                    sent_message_id=message['message_id']
                )
            else:
                error = self.KNOWN_ERROR_RESPONSE_CODES.get(
                    content,
                    'Unknown response code: %s' % (content,))
                yield self.publish_nack(message['message_id'], error)
        except Exception as ex:
            log.msg("Unexpected error %s" % repr(ex))

    @inlineCallbacks
    def handle_raw_inbound_message(self, request):
        try:
            for field in self.mandatory_inbound_message_fields:
                if not field in request.args:
                    raise MissingMessageField
            yield self.publish_message(
                transport_name=self.transport_name,
                transport_type='sms',
                to_addr=self.config['default_shortcode'],
                from_addr=request.args['msisdn'][0],
                content=request.args['message'][0],
                transport_metatdata={})
            request.setResponseCode(http.OK)
        except:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            request.setHeader('Content-Type', 'text/plain')
            request.write("UNEXPECTED ERROR: %s" % sys.exc_info()[0])

class AirtelBfHttpReceiveSMSResource(Resource):
    isLeaf = True
    
    def __init__(self, transport):
        self.transport = transport
        Resource.__init__(self)

    def render_GET(self, request):
        log.msg('got hit with %s' % request.args)
        self.transport.handle_raw_inbound_message(request)
        return ''
        
    
       