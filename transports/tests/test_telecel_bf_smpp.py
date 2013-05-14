from smpp.pdu_builder import SM2
from twisted.internet.defer import inlineCallbacks

from vumi.transports.smpp.clientserver.client import EsmeTransceiver
from vumi.transports.smpp.clientserver.tests.test_client import (
    EsmeGenericMixin, FakeEsmeMixin, EsmeTestCaseBase, EsmeReceiverMixin)

from transports.telecel_bf_smpp import EsmeDataTransceiverFactory

class FakeEsmeTransceiver(EsmeDataTransceiverFactory, FakeEsmeMixin):
    def __init__(self, *args, **kwargs):
        EsmeDataTransceiverFactory.__init__(self, *args, **kwargs)
        self.setup_fake()

    def send_pdu(self, pdu):
        return self.fake_send_pdu(pdu)


class EsmeDataTransmitterMixin(EsmeGenericMixin):
    """Receiver-side tests."""

    @inlineCallbacks
    def test_deliver_sm_message_payload(self):
        """A message in the `message_payload` field should be delivered."""
        esme = yield self.get_esme(
            data_sm=self.assertion_cb(u'hello', 'short_message'))
        sm = DataSM(1, short_message='')
        sm.add_message_payload(''.join('%02x' % ord(c) for c in 'hello'))
        yield esme.handle_data_sm(unpack_pdu(sm.get_bin()))


class EsmeTransceiverTestCase(EsmeTestCaseBase, EsmeDataTransmitterMixin):
    ESME_CLASS = FakeEsmeTransceiver


class DataSM(SM2):
    def __init__(self,
            sequence_number,
            **kwargs):
        super(SubmitSM, self).__init__('data_sm', sequence_number, **kwargs)