from uuid import uuid4
from datetime import datetime
from urllib import urlencode

from twisted.web import http
from twisted.web.resource import Resource
from twisted.internet.defer import inlineCallbacks, DeferredQueue

from vumi.transports.tests.test_base import TransportTestCase
from vumi.tests.utils import (get_stubbed_worker, TestResourceWorker,
                              RegexMatcher, UTCNearNow, MockHttpServer)
from vumi.utils import http_request_full
from vumi.message import TransportMessage, TransportEvent, TransportUserMessage

from transports.cm_nl_yo_ug_http import CmYoTransport


class CmYoTransportTestCase(TransportTestCase):

    transport_name = 'cm'
    transport_type = 'sms'
    transport_class = CmYoTransport
    
    send_path = '/sendsms'
    send_port = 9999

    yo_incomming_template = ('%s%s?sender=0041791234567&'
                             'code=%s&message=Hello+World')

    @inlineCallbacks
    def setUp(self):
        yield super(CmYoTransportTestCase, self).setUp()
        
        self.cmyo_sms_calls = DeferredQueue()
        self.mock_cmyo_sms = MockHttpServer(self.handle_request)
        yield self.mock_cmyo_sms.start()           
        
        self.config = {
            'transport_name': self.transport_name,
            'login': 'login',
            'password': 'password',
            'default_origin': "+313455",
            'customer_id': '3454',
            'receive_path': 'yo',
            'receive_port': 9998,
            'outbound_url': self.mock_cmyo_sms.url,            
        }
        self.transport = yield self.get_transport(self.config)
        self.transport_url = self.transport.get_transport_url()
        self.today = datetime.utcnow().date()

    @inlineCallbacks
    def tearDown(self):
        yield self.mock_cmyo_sms.stop()
        yield super(CmYoTransportTestCase, self).tearDown()

    def mkmsg_fail(self, user_message_id='1',
                   failure_level='', failure_code=0,
                   failure_reason='', transport_metadata={}):
        if transport_metadata is None:
            transport_metadata = {}
        return TransportEvent(
            event_id=RegexMatcher(r'^[0-9a-fA-F]{32}$'),
            event_type='delivery_report',
            delivery_status='failed',
            failure_level=failure_level,
            failure_code=failure_code,
            failure_reason=failure_reason,
            user_message_id=user_message_id,
            timestamp=UTCNearNow(),
            transport_name=self.transport_name,
            transport_metadata=transport_metadata)

    def mkmsg_in(self, content='Hello World',
                 from_addr='41791234567',
                 session_event=TransportUserMessage.SESSION_NONE,
                 message_id='abc', transport_type=None,
                 transport_metadata=None):
        if transport_type is None:
            transport_type = self.transport_type
        if transport_metadata is None:
            transport_metadata = {}
        return TransportUserMessage(
            from_addr='+41791234567',
            to_addr='9292',
            group=None,
            message_id=message_id,
            transport_name=self.transport_name,
            transport_type=transport_type,
            transport_metadata=transport_metadata,
            content=content,
            session_event=session_event,
            timestamp=UTCNearNow())

    #def make_resource_worker(self, msg, code=http.OK, send_id=None):
        #w = get_stubbed_worker(TestResourceWorker, {})
        #w.set_resources([
            #(self.send_path, TestResource, (msg, code, send_id))])
        #self._workers.append(w)
        #return w.startWorker()

    def handle_request(self, request):
        self.cmyo_sms_calls.put(request)
        return ''

    @inlineCallbacks
    def test_sending_sms(self):
        yield self.dispatch(self.mkmsg_out(to_addr='+41791234567'))
        req = yield self.cmyo_sms_calls.get()
        self.assertEqual(req.path, '/')
        self.assertEqual(req.method, 'POST')
        [smsg] = self.get_dispatched_events()
        self.assertEqual(self.mkmsg_delivery(user_message_id='1',
                                             sent_message_id='1'),
                         smsg)

    #@inlineCallbacks
    #def test_sending_sms_http_failure(self):
        #mocked_message = "timeout"
        #mocked_error = http.REQUEST_TIMEOUT

        ##HTTP response
        #yield self.make_resource_worker(mocked_message, mocked_error)
        #yield self.dispatch(self.mkmsg_out(to_addr='256788601462'))

        #[smsg] = self.get_dispatched('cm.event')
        #self.assertEqual(
            #self.mkmsg_fail(failure_level='http',
                            #failure_code=http.REQUEST_TIMEOUT,
                            #failure_reason='timeout'),
            #TransportMessage.from_json(smsg.body))

    #@inlineCallbacks
    #def test_sending_sms_service_failure(self):
        #mocked_message = "Error: ERROR Unknown error"

        ##HTTP response
        #yield self.make_resource_worker(mocked_message)
        #yield self.dispatch(self.mkmsg_out(to_addr='788601462'))
        #[smsg] = self.get_dispatched('cm.event')
        #self.assertEqual(
            #self.mkmsg_fail(failure_level='service',
                            #failure_reason="Error: ERROR Unknown error"),
            #TransportMessage.from_json(smsg.body))

    def mkurl_raw(self, **params):
        return self.yo_incomming_template % (
            self.transport_url,
            self.config['receive_path'],
            '')     

    @inlineCallbacks
    def test_receiving_sms(self):
        url = self.mkurl_raw()
        response = yield http_request_full(url, method='GET')
        [smsg] = self.get_dispatched_messages()

        self.assertEqual(response.code, http.OK)
        self.assertEqual('Hello World', smsg['content'])
        self.assertEqual('+313455', smsg['to_addr'])
        self.assertEqual('+41791234567', smsg['from_addr'])


class TestResource(Resource):
    isLeaf = True

    def __init__(self, message, code=http.OK, send_id=None):
        self.message = message
        self.code = code
        self.send_id = send_id

    def render_GET(self, request):
        request.setResponseCode(self.code)
        return self.message

    def render_POST(self, request):
        request.setResponseCode(self.code)
        return self.message
