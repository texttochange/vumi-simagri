from twisted.internet.defer import inlineCallbacks

#from vumi.tests.utils import VumiWorkerTestCase
from vumi.dispatchers.tests.test_base import TestTransportToTransportRouter
from vumi.dispatchers import BaseDispatchWorker

from dispatchers import TranportToTransportToAddrMultiplexRouter

class TestTransportToTransportToAddrMultiplexRouter(TestTransportToTransportRouter):

    @inlineCallbacks
    def setUp(self):
        yield super(TestTransportToTransportRouter, self).setUp()
        config = {
            "transport_names": [
                "transport_1",
                "transport_2",
                "transport_3",
                "transport_muxed"
                ],
            "exposed_names": [],
            "router_class": "dispatchers.TranportToTransportToAddrMultiplexRouter",
            "toaddr_mappings": {
                "^1": "transport_1",
                "^2": "transport_2",
                "^3": "transport_3",
                },
            "route_mappings": {
                "transport_1": ["transport_muxed"],
                "transport_2": ["transport_muxed"],
                "transport_3": ["transport_muxed"]
                }
            }
        self.worker = yield self.get_worker(config, BaseDispatchWorker)
    
    @inlineCallbacks
    def test_inbound_message_routing(self):
        #test from the tansports to the transport
        msg = self.mkmsg_in(transport_name='transport_1')
        yield self.dispatch(msg, 'transport_1.inbound')
        self.assert_messages('transport_muxed.outbound', [msg])
        self.assert_no_messages('transport_2.outbound', 'transport_2.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_1.outbound',
                                'transport_muxed.inbound')

    @inlineCallbacks
    def test_outbound_message_routing(self):
        #test from the tansport to the multex transport
        msg = self.mkmsg_in(transport_name='transport_muxed', to_addr='123')
        yield self.dispatch(msg, 'transport_muxed.inbound')
        self.assert_messages('transport_1.outbound', [msg])
        self.assert_no_messages('transport_2.outbound', 'transport_2.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_1.inbound')
        
        self.clear_dispatched()
        msg = self.mkmsg_in(transport_name='transport_muxed', to_addr='234')
        yield self.dispatch(msg, 'transport_muxed.inbound')
        self.assert_messages('transport_2.outbound', [msg])
        self.assert_no_messages('transport_1.outbound', 'transport_1.inbound',
                                'transport_3.outbound', 'transport_3.inbound',
                                'transport_2.inbound')