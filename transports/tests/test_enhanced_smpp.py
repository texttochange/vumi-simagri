from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from vumi.transports.tests.test_base import TransportTestCase
from vumi.transports.smpp.tests.test_smpp import SmppTransportTestCase
from vumi.transports.smpp.clientserver.config import ClientConfig
from vumi.transports.smpp.service import SmppService
from vumi.transports.smpp.clientserver.tests.utils import SmscTestServer
from vumi.message import TransportUserMessage
from vumi.tests.utils import FakeRedis

from transports.enhanced_smpp import EnhancedSmppTransport, EnhancedClientConfig


class EnhancedSmppTransportTestCase(SmppTransportTestCase):
    transport_class = EnhancedSmppTransport

    @inlineCallbacks
    def setUp(self):
        super(SmppTransportTestCase, self).setUp()
        self.config = {
            "transport_name": self.transport_name,
            "system_id": "vumitest-vumitest-vumitest",
            "host": "host",
            "port": "port",
            "password": "password",
            "smpp_bind_timeout": 12,
            "smpp_enquire_link_interval": 123,
            "third_party_id_expiry": 3600,
            "data_coding": 3,
        }
        self.clientConfig = EnhancedClientConfig.from_config(self.config)
        # hack a lot of transport setup
        self.transport = yield self.get_transport(self.config, start=False)
        self.transport.esme_client = None
        yield self.transport.startWorker()

        self._make_esme()
        self.transport.esme_client = self.esme
        self.transport.esme_connected(self.esme)

    @inlineCallbacks
    def test_encoding_message(self):
        # Sequence numbers are hardcoded, assuming we start fresh from 0.
        message1 = self.mkmsg_out(u"message @ 1 \xe9", message_id='444')
        yield self.dispatch(message1)

        self.assert_sent_contents(["message @ 1 \xe9"])
        pdu_contents = [p.obj['body']['mandatory_parameters']['data_coding']
                        for p in self.esme.sent_pdus]
        self.assertEqual([3], pdu_contents)        