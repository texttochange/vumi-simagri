from twisted.web import http
from twisted.web.resource import Resource
from twisted.internet.defer import inlineCallbacks, DeferredQueue

from vumi.tests.utils import MockHttpServer
from vumi.transports.tests.test_base import TransportTestCase
from vumi.message import TransportMessage

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
            'url': 'http://localhost:%s%s' % (self.send_port, self.send_path),
            'receive_path': '/sendsms',
            'receive_port': 9998
            }
        self.worker = yield self.get_transport(self.config)

    def handle_request(self, request):
        self.simagri_sms_calls.put(request)
        return ''

    #def make_resource_worker(self, msg, code=http.OK, send_id=None):
        #w = get_stubbed_worker(TestResourceWorker, {})
        #w.set_resources([
            #(self.send_path, TestResource, (msg, code, send_id))])
        #self._workers.append(w)
        #return w.startWorker()

    @inlineCallbacks
    def test_sending_sms(self):
        self.make_resource_worker("")
        yield self.dispatch(self.mkmsg_out("+2261"))
        req = yield self.simagri_sms_calls.get()
        self.assertEqual(req.path, '/')
        self.assertEqual(req.method, 'GET')
        self.assertEqual({
            'username': ['other-user'],
            'password': ['other-pass'],
            'source': ['9292'],
            'destination': ['2371234567'],
            'message': ['hello world'],
            }, req.args)        
        [smsg] = self.get_dispatched_events()
        self.assertEqual(self.mkmsg_ack(user_message_id=1),
                         TransportMessage.from_json(smsg))

    def test_sending_sms_failed(self):
        pass

    def test_receiving_sms(self):
        url = ("http://localhost:%s/%s?message?message=%s&to_addr=%s&from_addr=%s" % 
               (self.config['receive_port'],
                self.config['receive_path'],
                'Hello',
                '+2261',
                '2323'))
        response = yield http_request_full(url, method='GET')
        [smsg] = self.get_dispatched('cm.inbound')

        self.assertEqual(response.code, http.OK)
        msg = TransportMessage.from_json(smsg.body)
        self.assertEqual('Hello',
                         msg['content'])
        self.assertEqual('+2261',
                         msg['to_addr'])
        self.assertEqual('2323',
                         msg['from_addr'])

    def test_receiving_sms_fail(self):
        pass


class TestResource(Resource):
    isLeaf = True

    def __init__(self, message, code=http.OK, send_id=None):
        self.message = message
        self.code = code
        self.send_id = send_id

    def render_GET(self, request):
        request.setResponseCode(self.code)
        return self.message