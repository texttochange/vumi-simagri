import sys
from urllib import urlencode

from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from twisted.web.resource import Resource
from twisted.web import http

from vumi.transports.base import Transport
from vumi.utils import http_request_full
from vumi.errors import MissingMessageField
from vumi.log import log


class SimagriHttpTransport(Transport):
    
    mandatory_message_fields = ['message', 'from_addr', 'to_addr']
    
    @inlineCallbacks
    def setup_transport(self):
        log.msg("Setup yo transport %s" % self.config)        
        #self._resources = []
        self.web_resource = yield self.start_web_resources(
            [
                (SimagriReceiveSMSResource(self), self.config['receive_path'])
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
                'message': (message['content'] or '').encode("utf8"),
                'from_addr': message['from_addr']
            }
            log.msg('Hitting %s with %s' % (self.config['outbound_url'], urlencode(params)))
            response = yield http_request_full(
                "%s?%s" % (self.config['outbound_url'], urlencode(params)),
                method='GET')
            log.msg("Response: (%s) %r" % (response.code, response.delivered_body))
            content = response.delivered_body.strip()            
            
            if response.code == 200:
                yield self.publish_ack(
                    user_message_id=message['message_id'],
                    sent_message_id=message['message_id'])
            else:
                error = self.KNOWN_ERROR_RESPONSE_CODES.get(
                    content,
                    'Unknown response code: %s' % (content,))
                yield self.publish_nack(message['message_id'], error)
        except Exception as ex:
            log.msg("Unexpected error %s" % repr(ex)) 
    
    def phone_format_from_simagri(self, phone):
        return phone        
    
    @inlineCallbacks
    def handle_raw_inbound_message(self, request):
        try:
            for field in self.mandatory_message_fields:
                if not field in request.args:
                    raise MissingMessageField(field)                       
            yield self.publish_message(
                transport_name=self.transport_name,
                transport_type='sms',
                to_addr=self.phone_format_from_simagri(request.args['to_addr'][0]),
                from_addr=request.args['from_addr'][0],
                content=request.args['message'][0],
                transport_metadata={})
            request.setResponseCode(http.OK)
        except MissingMessageField as e:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            request.setHeader('Content-Type', 'text/plain')
            request.write("MISSING FIELD: %s" % str(e))
        except:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            request.setHeader('Content-Type', 'text/plain')
            request.write("UNEXPECTED ERROR: %s" % sys.exc_info()[0])


class SimagriReceiveSMSResource(Resource):
    isLeaf = True
    
    def __init__(self, transport):
        self.transport = transport
        Resource.__init__(self)

    def render_GET(self, request):
        log.msg('got hit with %s' % request.args)
        self.transport.handle_raw_inbound_message(request)
        return ''
