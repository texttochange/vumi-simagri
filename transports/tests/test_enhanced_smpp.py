from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from vumi.transports.tests.test_base import TransportTestCase
from vumi.transports.smpp.tests.test_smpp import SmppTransportTestCase
from vumi.transports.smpp.clientserver.config import ClientConfig
from vumi.transports.smpp.service import SmppService
from vumi.transports.smpp.clientserver.tests.utils import SmscTestServer
from vumi.message import TransportUserMessage
from vumi.tests.utils import FakeRedis

from transports.enhanced_smpp import EnhancedSmppTransport


class EnhancedSmppTransportTestCase(SmppTransportTestCase):
    transport_class = EnhancedSmppTransport

    @inlineCallbacks
    def setUp(self):
        super(EnhancedSmppTransportTestCase, self).setUp()
        self.config = {
            "transport_name": self.transport_name,
            "system_id": "vumitest-vumitest-vumitest",
            "host": "host",
            "port": "port",
            "password": "password",
            "smpp_bind_timeout": 12,
            "smpp_enquire_link_interval": 123,
            "third_party_id_expiry": 3600,
            "submit_sm_encoding": "latin1",
            "submit_sm_data_encoding": 3,
        }
        self.clientConfig = ClientConfig.from_config(self.config)
        # hack a lot of transport setup
        self.transport = yield self.get_transport(self.config, start=False)
        self.transport.esme_client = None
        yield self.transport.startWorker()

        self._make_esme()
        self.transport.esme_client = self.esme
        self.transport.esme_connected(self.esme)
