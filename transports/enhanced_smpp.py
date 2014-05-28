from vumi import log
from vumi.utils import get_operator_number
from vumi.transports.smpp import SmppTransport
from vumi.transports.smpp.clientserver.config import ClientConfig
from vumi.message import TransportUserMessage


class EnhancedSmppTransport(SmppTransport):
    
    codecs = {
        0: 'utf-8',
        1: 'ascii',
        3: 'latin1',
        8: 'utf-16be',  # Actually UCS-2, but close enough.
    }    
    
    def validate_config(self):
        self.client_config = EnhancedClientConfig.from_config(self.config)
        self.throttle_delay = float(self.config.get('throttle_delay', 0.1))        
        
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
                short_message=text.encode(self.codecs[self.client_config.data_coding]),
                destination_addr=str(to_addr),
                source_addr=route,
                message_type=message['transport_type'],
                continue_session=continue_session,
                session_info=message['transport_metadata'].get('session_info'),
                )


class EnhancedClientConfig(ClientConfig):

    def __init__(self, host, port, system_id, password, 
                 data_coding=0, system_type="", interface_version="34", 
                 service_type="",
                 dest_addr_ton=0, dest_addr_npi=0,
                 source_addr_ton=0, source_addr_npi=0,
                 registered_delivery=0, smpp_bind_timeout=30,
                 smpp_enquire_link_interval=55.0,
                 initial_reconnect_delay=5.0,
                 delivery_report_regex=None,
                 data_coding_overrides=None,
                 send_long_messages=False,):
        super(EnhancedClientConfig, self).__init__(host, port, system_id, password, 
                                                   system_type, interface_version, 
                                                   service_type, dest_addr_ton, dest_addr_npi,
                                                   source_addr_ton, source_addr_npi,
                                                   registered_delivery, smpp_bind_timeout,
                                                   smpp_enquire_link_interval,
                                                   initial_reconnect_delay,
                                                   delivery_report_regex,
                                                   data_coding_overrides,
                                                   send_long_messages)
        self.data_coding = int(data_coding)
