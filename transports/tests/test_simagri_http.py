from urllib import urlencode

from twisted.web import http
from twisted.web.resource import Resource
from twisted.internet.defer import inlineCallbacks, DeferredQueue

from vumi.tests.utils import MockHttpServer
from vumi.transports.tests.test_base import TransportTestCase
from vumi.message import TransportMessage
from vumi.utils import http_request_full

from transports.simagri_http import SimagriHttpTransport

class SimagriTransportTestCase(TransportTestCase):
    
    transport_name = 'simagri'
    transport_type = 'sms'
    transport_class = SimagriHttpTransport
    
    send_path = '/sendsms/index'
    send_port = 9999
    
    @inlineCallbacks
    def setUp(self):
        yield super(SimagriTransportTestCase, self).setUp()

        self.simagri_sms_calls = DeferredQueue()
        self.mock_simagri_sms = MockHttpServer(self.handle_request)
        yield self.mock_simagri_sms.start()        
        
        self.config = {
            'transport_name': self.transport_name,
            'receive_path': 'sendsms',
            'receive_port': 9998,
            'outbound_url': self.mock_simagri_sms.url
            }
        self.transport = yield self.get_transport(self.config)
        self.transport_url = self.transport.get_transport_url()

    @inlineCallbacks
    def tearDown(self):
        yield self.mock_simagri_sms.stop()
        yield super(SimagriTransportTestCase, self).tearDown()

    def handle_request(self, request):
        self.simagri_sms_calls.put(request)
        return ''

    @inlineCallbacks
    def test_sending_sms(self):
        yield self.dispatch(self.mkmsg_out(from_addr="+2261"))
        req = yield self.simagri_sms_calls.get()
        self.assertEqual(req.path, '/')
        self.assertEqual(req.method, 'GET')
        self.assertEqual({
            'from_addr': ['+2261'],
            'message': ['hello world'],
            }, req.args)        
        [smsg] = self.get_dispatched_events()
        self.assertEqual(self.mkmsg_ack(user_message_id='1',
                                        sent_message_id='1'),
                         smsg)

    def mkurl_raw(self, **params):
        return '%s%s?%s' % (
            self.transport_url,
            self.config['receive_path'],
            urlencode(params))    

    def mkurl(self, content, to_addr, from_addr, **kw):
        params = {
            'message': content,
            'to_addr': to_addr,
            'from_addr': from_addr,
        }
        params.update(kw)
        return self.mkurl_raw(**params)

    @inlineCallbacks
    def test_receiving_sms(self):
        url = self.mkurl('Hello', '+2261', '2323')
        response = yield http_request_full(url, method='GET')
        [smsg] = self.get_dispatched_messages()

        self.assertEqual(response.code, http.OK)
        self.assertEqual('Hello', smsg['content'])
        self.assertEqual('+2261', smsg['to_addr'])
        self.assertEqual('2323', smsg['from_addr'])

    @inlineCallbacks
    def test_receiving_sms_fail(self):
        params = {
            'message': 'Hello',
            'to_addr': '+2261',
        }
        url = self.mkurl_raw(**params)        
        response = yield http_request_full(url, method='GET')
        self.assertEqual(0, len(self.get_dispatched_messages()))
        self.assertEqual(response.code, http.INTERNAL_SERVER_ERROR)

class TestResource(Resource):
    isLeaf = True

    def __init__(self, message, code=http.OK, send_id=None):
        self.message = message
        self.code = code
        self.send_id = send_id

    def render_GET(self, request):
        request.setResponseCode(self.code)
        return self.message