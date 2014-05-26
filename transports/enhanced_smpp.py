from vumi import log
from vumi.utils import get_operator_number
from vumi.transports.smpp import SmppTransport
from vumi.message import TransportUserMessage


class EnhancedSmppTransport(SmppTransport):
    
    def setup_transport(self):
        self.submit_sm_encoding = self.config.get("submit_sm_encoding", "utf-8");
        self.submit_sm_data_encoding = self.config.get("submit_sm_data_encoding", 0);
        super(EnhancedSmppTransport, self).setup_transport()

    def send_smpp(self, message):
        # first do a lookup in our YAML to see if we've got a source_addr
        # defined for the given MT number, if not, trust the from_addr
        # in the message
        to_addr = message['to_addr']
        from_addr = message['from_addr']
        text = message['content']
        continue_session = (
            message['session_event'] != TransportUserMessage.SESSION_CLOSE)
        route = get_operator_number(to_addr,
                self.config.get('COUNTRY_CODE', ''),
                self.config.get('OPERATOR_PREFIX', {}),
                self.config.get('OPERATOR_NUMBER', {})) or from_addr
        return self.esme_client.submit_sm(
                short_message=text.encode(self.submit_sm_encoding),
                data_encoding=self.submit_sm_data_encoding,
                destination_addr=str(to_addr),
                source_addr=route,
                message_type=message['transport_type'],
                continue_session=continue_session,
                session_info=message['transport_metadata'].get('session_info'),
                )
