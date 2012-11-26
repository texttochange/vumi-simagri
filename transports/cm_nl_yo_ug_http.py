# -*- test-case-name: tests.test_yo_ug_http -*-

import re

from xml.etree import ElementTree

from urllib import urlencode, unquote
from urlparse import parse_qs

from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from twisted.internet.error import ConnectionRefusedError
from twisted.web import http
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer

from vumi.transports.base import Transport
from vumi.utils import http_request_full, normalize_msisdn


##This transport is supposed to send and receive sms in 2 different ways.
##To send sms we use the CM API
##To receive sms we use the YO Interface to forward the sms
class CmYoTransport(Transport):

    #def mkres(self, cls, publish_func, path_key):
        #resource = cls(self.config, publish_func)
        #self._resources.append(resource)
        #return (resource, self.config['receive_path'])

    @inlineCallbacks
    def setup_transport(self):
        log.msg("Setup yo transport %s" % self.config)
        self._resources = []
        self.web_resource = yield self.start_web_resources(
            [
                (YoReceiveSMSResource(self), self.config['receive_path'])
            ],
            self.config['receive_port'])

    @inlineCallbacks
    def teardown_transport(self):
        yield seld.web_resource.loseConnection()

    def get_transport_url(self, suffix=''):
        addr = self.web_resource.getHost()
        return "http://%s:%s/%s" % (addr.host, addr.port, suffix.lstrip('/'))

    @inlineCallbacks
    def handle_outbound_message(self, message):
        log.msg("Outbound message to be processed %s" % repr(message))
        try:
            cmparser = CMXMLParser()
            params = cmparser.build({
                'customer_id': self.config['customer_id'],
                'login': self.config['login'],
                'password': self.config['password'],
                'from_addr': self.config['default_origin'],
                'to_addr': message['to_addr'],
                'content': message['content']})
            log.msg('Hitting %s with %s' % (self.config['outbound_url'], urlencode(params)))
            response = yield http_request_full(
                self.config['url'],
                params,
                {'User-Agent': ['Vumi CM YO Transport'],
                 'Content-Type': ['application/json;charset=UTF-8'], },
                method='POST')
            log.msg("Response: (%s) %r" % (response.code, response.delivered_body))
            content = response.delivered_body.strip()            

            if response.code != 200 or response.delivered_body:
                error = self.KNOWN_ERROR_RESPONSE_CODES.get(content,
                                                            'Unknown response code: %s' % (content,))
                yield self.publish_nack(message['message_id'], error)
                return    
            yield self.publish_ack(user_message_id=message['message_id'],
                                   sent_message_id=message['message_id'])
        except Exception as ex:
            log.msg("Unexpected error %s" % repr(ex))
            
    def phone_format_from_yo(self, phone):
        regex = re.compile('^[(00)(\+)]')
        regex_single = re.compile('^0')
        phone = re.sub(regex, '', phone)
        phone = re.sub(regex_single, '', phone)
        return ('+%s' % phone)

    @inlineCallbacks
    def handle_raw_inbound_message(request):
        yield self.publish_func(
            transport_name=self.transport_name,
            transport_type='sms',
            to_addr=(request.args['code'][0] if request.args['code'][0]!='' else self.config['default_origin']),
            from_addr=self.phone_format_from_yo(request.args['sender'][0]),
            content=request.args['message'][0],
            transport_metadata={})


class YoReceiveSMSResource(Resource):
    isLeaf = True

    def __init__(self, transport):
        self.transport = transport
        Resource.__init__(self)

    def render_GET(self, request):
        log.msg('got hit with %s' % request.args)
        try:
            self.transport.handle_raw_inbound_message(request)
            request.setResponseCode(http.OK)
            request.setHeader('Content-Type', 'text/plain')           
        except:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            request.setHeader('Content-Type', 'text/plain')                        
            log.msg("Error processing the request: %s" % (request,))
        return ''


class CMXMLParser():

    def build(self, messagedict):
        messages = ElementTree.Element('MESSAGES')
        customer = ElementTree.SubElement(messages, 'CUSTOMER')
        customer.set('ID', messagedict['customer_id'])
        user = ElementTree.SubElement(messages, 'USER')
        user.set('LOGIN', messagedict['login'])
        user.set('PASSWORD', messagedict['password'])
        msg = ElementTree.SubElement(messages, 'MSG')
        origin = ElementTree.SubElement(msg, 'FROM')
        origin.text = messagedict['from_addr']
        body = ElementTree.SubElement(msg, 'BODY')
        body.set('TYPE', 'TEXT')
        body.set('HEADER', '')
        body.text = messagedict['content']
        to = ElementTree.SubElement(msg, 'TO')
        to.text = messagedict['to_addr']

        return ElementTree.tostring(messages)
