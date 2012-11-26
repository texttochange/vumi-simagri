from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from twisted.web.resource import Resource

from vumi.transports.base import Transport

class SimagriHttpTransport(Transport):
    
    @inlineCallbacks
    def setup_transport(self):
        log.msg("Setup yo transport %s" % self.config)        
        self._resources = []
        self.web_resource = yield self.start_web_resources(
            [
                (SimagriReceiveSMSResource(self), self.config['receive_path'])
            ],
            self.config['receive_port'])
    
    @inlineCallbacks
    def teardown_transport(self):
        yield self.web_resource.loseConnection()    

    @inlineCallbacks
    def handle_outbound_message(self, message):
        log.msg("Outbound message to be processed %s" % repr(message))
        try:
            params = {
                'message': message['content'],
                'from_addr': message['from_addr']
            }
            log.msg('Hitting %s with %s' % (self.config['url'], urlencode(params)))
    
            response = yield http_request_full(
                "%s?%s" % (self.config['url'], urlencode(params)),
                "",
                {'User-Agent': ['Vumi Simagri Transport'],
                 'Content-Type': ['application/json;charset=UTF-8'], },
                'GET')
    
            if response.code == 200:
                self.publish_ack(user_message_id=message['message_id'],
                                 sent_message_id=message['message_id'])
                return
            log.msg("Http Error %s: %s" % (response.code, response.delivered_body))
        except Exception as ex:
            log.msg("Unexpected error %s" % repr(ex)) 
    
    def handle_raw_inbound_message(request):
        self.publish_message(
            transport_name=self.transport_name,
            transport_type='sms',
            to_addr=self.phone_format_from_smagri(request.args['to_addr'][0]),
            from_addr=request.args['from_addr'][0],
            content=request.args['message'][0],
            transport_metadata={}
        )            
    

class SimagriReceiveSMSResource(Resource):
    isLeaf = True
    
    def __init__(self, transport):
        self.transport = transport
        Resource.__init__(self)

    def phone_format_from_simagri(phone):
        return phone

    @inlineCallbacks
    def do_render(self, request):
        log.msg('got hit with %s' % request.args)
        request.setHeader("content-type", self.transport.content_type)
        try:
            self.transport.handle_raw_inbound_message(request)
            request.setResponseCode(http.OK)
            request.setHeader('Content-Type', 'text/plain')
        except:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            log.msg("Error processing the request: %s" % (request,))                
        request.finish()