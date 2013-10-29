from smpp.pdu_builder import SM2, SubmitSM
from smpp.pdu import unpack_pdu
from twisted.internet.defer import inlineCallbacks

from vumi.transports.smpp.clientserver.client import EsmeTransceiver
from vumi.transports.smpp.clientserver.tests.test_client import (
    EsmeGenericMixin, FakeEsmeMixin, EsmeTestCaseBase, EsmeReceiverMixin)
from vumi.transports.smpp.clientserver.config import ClientConfig

from transports.telecel_bf_smpp import EsmeDataTransceiver


class FakeEsmeDataTransceiver(EsmeDataTransceiver, FakeEsmeMixin):

    def __init__(self, *args, **kwargs):
        EsmeDataTransceiver.__init__(self, *args, **kwargs)
        self.setup_fake()

    def send_pdu(self, pdu):
        return self.fake_send_pdu(pdu)


class EsmeTransceiverTestCase(EsmeTestCaseBase):
    ESME_CLASS = FakeEsmeDataTransceiver

    @inlineCallbacks
    def test_data_sm_message_payload(self):
        """A message in the `message_payload` field should be delivered."""
        esme = yield self.get_esme(
            deliver_sm=self.assertion_cb(u'hello', 'short_message'))
        sm = DataSM(1, short_message='')
        sm.add_message_payload(''.join('%02x' % ord(c) for c in 'hello'))
        yield esme.handle_data_sm(unpack_pdu(sm.get_bin()))

    @inlineCallbacks
    def test_data_sm_message_payload_None(self):
        """A message in the `message_payload` field should be delivered."""
        esme = yield self.get_esme(
            deliver_sm=self.assertion_cb(u'', 'short_message'))
        sm = DataSM(1, short_message='')
        sm.add_message_payload('')
        yield esme.handle_data_sm(unpack_pdu(sm.get_bin()))


class DataSM(SM2):
    
    def __init__(self,
            sequence_number,
            **kwargs):
        super(DataSM, self).__init__('data_sm', sequence_number, **kwargs)
