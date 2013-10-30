from twisted.internet.defer import inlineCallbacks

from vumi.tests.utils import VumiWorkerTestCase
from vumi.dispatchers import BaseDispatchWorker

from dispatchers import TranportToTransportToAddrMultiplexRouter


class TestTransportToTransportRouter(VumiWorkerTestCase):

    def dispatch(self, message, rkey=None, exchange='vumi'):
        if rkey is None:
            rkey = self.rkey('outbound')
        self._amqp.publish_message(exchange, rkey, message)
        return self._amqp.kick_delivery()

    def assert_messages(self, rkey, msgs):
        self.assertEqual(msgs, self._amqp.get_messages('vumi', rkey))
  
    def assert_no_messages(self, *rkeys):
        for rkey in rkeys:
            self.assertEqual([], self._amqp.get_messages('vumi', rkey))

    def clear_dispatched(self):
        self._amqp.dispatched = {}        


class TestTransportToTransportToAddrMultiplexRouter(TestTransportToTransportRouter):

    @inlineCallbacks
    def setUp(self):
        yield super(TestTransportToTransportRouter, self).setUp()
        config = {
            "transport_names": [
                "transport_1",
                "transport_2",
                "transport_3",
                "transport_muxed",
                "transport_4",
                ],
            "exposed_names": [],
            "router_class": "dispatchers.TranportToTransportToAddrMultiplexRouter",
            "country_code": "226",
            "toaddr_mappings": {
                "transport_1": ["1[1-4]", "1[8-9]"],
                "transport_2": ["2"],
                "transport_3": ["3"],
                },
            "toaddr_fallback" : "transport_4",
            "route_mappings": {
                "transport_1": ["transport_muxed"],
                "transport_2": ["transport_muxed"],
                "transport_3": ["transport_muxed"],
                "transport_4": ["transport_muxed"]
                }
            }
        self.worker = yield self.get_worker(config, BaseDispatchWorker)
    
    @inlineCallbacks
    def test_inbound_message_routing(self):
        #test from the tansports to the transport
        msg = self.mkmsg_in(transport_name='transport_1', to_addr='2261')
        yield self.dispatch(msg, 'transport_1.inbound')
        self.assert_messages('transport_muxed.outbound', [msg])
        self.assert_no_messages('transport_2.outbound', 'transport_2.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_1.outbound',
                                'transport_4.outbound', 'transport_4.inbound',
                                'transport_muxed.inbound')

    @inlineCallbacks
    def test_outbound_message_routing(self):
        #test from the tansport to the multex transport
        msg = self.mkmsg_in(transport_name='transport_muxed', to_addr='226123')
        yield self.dispatch(msg, 'transport_muxed.inbound')
        self.assert_messages('transport_1.outbound', [msg])
        self.assert_no_messages('transport_2.outbound', 'transport_2.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_1.inbound',
                                'transport_4.inbound', 'transport_4.outbound')
        
        self.clear_dispatched()
        msg = self.mkmsg_in(transport_name='transport_muxed', to_addr='226234')
        yield self.dispatch(msg, 'transport_muxed.inbound')
        self.assert_messages('transport_2.outbound', [msg])
        self.assert_no_messages('transport_1.outbound', 'transport_1.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_2.inbound', 
                                'transport_4.inbound', 'transport_4.outbound')

    @inlineCallbacks
    def test_outbound_message_routing_catchall_rule(self):
        #test from the tansport to the multex transport
        msg = self.mkmsg_in(transport_name='transport_muxed', to_addr='22616')
        yield self.dispatch(msg, 'transport_muxed.inbound')
        self.assert_messages('transport_4.outbound', [msg])
        self.assert_no_messages('transport_2.outbound', 'transport_2.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_1.inbound', 'transport_1.outbound',
                                'transport_4.inbound')


class TestTransportToTransportToAddrMultiplexRouterNoFallback(TestTransportToTransportRouter):

    @inlineCallbacks
    def setUp(self):
        yield super(TestTransportToTransportToAddrMultiplexRouterNoFallback, self).setUp()
        config = {
            "transport_names": [
                "transport_1",
                "transport_2",
                "transport_3",
                "transport_muxed",
                ],
            "exposed_names": [],
            "router_class": "dispatchers.TranportToTransportToAddrMultiplexRouter",
            "country_code": "226",
            "toaddr_mappings": {
                "transport_1": ["1[1-4]", "1[8-9]"],
                "transport_2": ["2"],
                "transport_3": ["3"],
                },
            "route_mappings": {
                "transport_1": ["transport_muxed"],
                "transport_2": ["transport_muxed"],
                "transport_3": ["transport_muxed"],
                }
            }
        self.worker = yield self.get_worker(config, BaseDispatchWorker)    

    @inlineCallbacks
    def test_outbound_message_routing_no_catchall_rule(self):
        #test from the tansport to the multex transport
        msg = self.mkmsg_in(transport_name='transport_muxed', to_addr='22616')
        yield self.dispatch(msg, 'transport_muxed.inbound')
        self.assert_no_messages('transport_2.outbound', 'transport_2.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_1.inbound', 'transport_1.outbound')
