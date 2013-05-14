from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial.unittest import TestCase

from middlewares.address_middleware import AddressMiddleware


def mk_msg(to_addr='unknown', from_addr='unknown'):
    return {
        'to_addr': to_addr,
        'from_addr': from_addr,
    }


class AddressTestCase(TestCase):
    
    def setUp(self):
        dummy_worker = object()
        self.mw = AddressMiddleware('mw1', {}, dummy_worker)
        self.mw.setup_middleware()

    def test_handle_inbound(self):
        msg_1 = mk_msg(from_addr="254888")
        msg_1 = self.mw.handle_inbound(msg_1 , 'dummy_endpoint')
        self.assertEqual(msg_1['from_addr'], '254888')
        
        msg_2 = mk_msg(from_addr="+254888")
        msg_2 = self.mw.handle_inbound(msg_2 , 'dummy_endpoint')
        self.assertEqual(msg_2['from_addr'], '+254888')

    def test_handle_outbound(self):
        msg_2 = mk_msg(from_addr="+318888")
        msg_2 = self.mw.handle_outbound(msg_2 , 'dummy_endpoint')
        self.assertEqual(msg_2['from_addr'], '+318888')


class VusionAddressRemoveOutboundPlusTestCase(TestCase):
    
    def setUp(self):
        dummy_worker = object()
        self.mw = AddressMiddleware(
            'mw1',
            {
                'to_addr': {'plus_outbound': 'trim'},
                'from_addr': {'plus_outbound': 'trim'}
             },
            dummy_worker)
        self.mw.setup_middleware()

    def test_handle_outbound(self):
        msg_1 = mk_msg(to_addr="+256", from_addr="+256")
        msg_1 = self.mw.handle_outbound(msg_1 , 'dummy_endpoint')
        self.assertEqual(msg_1['to_addr'], '256')
        self.assertEqual(msg_1['from_addr'], '256')


class VusionAddressEnsurePlusOutboundTestCase(TestCase):
    
    def setUp(self):
        dummy_worker = object()
        self.mw = AddressMiddleware(
            'mw1',
            {
                'to_addr': {'plus_outbound': 'ensure'},
                'from_addr': {'plus_outbound': 'ensure'}
             },
            dummy_worker)
        self.mw.setup_middleware()

    def test_handle_outbound(self):
        msg_1 = mk_msg(to_addr="256", from_addr="256")
        msg_1 = self.mw.handle_outbound(msg_1 , 'dummy_endpoint')
        self.assertEqual(msg_1['to_addr'], '+256')
        self.assertEqual(msg_1['from_addr'], '+256')
    
        msg_2 = mk_msg(to_addr="+256", from_addr="+256")
        msg_2 = self.mw.handle_outbound(msg_2 , 'dummy_endpoint')
        self.assertEqual(msg_2['to_addr'], '+256')
        self.assertEqual(msg_2['from_addr'], '+256')    


class VusionAddressRemoveInboundPlusTestCase(TestCase):
    
    def setUp(self):
        dummy_worker = object()
        self.mw = AddressMiddleware(
            'mw1',
            {
                'to_addr': {'plus_inbound': 'trim'},
                'from_addr': {'plus_inbound': 'trim'}
                },
            dummy_worker)
        self.mw.setup_middleware()

    def test_handle_inbound(self):
        msg_1 = mk_msg(to_addr="+256", from_addr="+256")
        msg_1 = self.mw.handle_inbound(msg_1 , 'dummy_endpoint')
        self.assertEqual(msg_1['to_addr'], '256')
        self.assertEqual(msg_1['from_addr'], '256')
