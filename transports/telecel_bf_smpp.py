
from smpp.pdu_builder import DeliverSMResp

from vumi.transports.smpp.clientserver.client import unpacked_pdu_opts
from vumi.transports.smpp.clientserver.client import EsmeTransceiver
from vumi.transports.smpp import SmppTransport


class TelecelBfSmppTransport(SmppTransport):
    
    def make_factory(self):
        return EsmeDataTransceiverFactory(
            self.client_config,
            self.r_server,
            self.esme_callbacks)


class EsmeDataTransceiverFactory(EsmeTransceiver):

    ## Receiving sms
    def handle_data_sm(self):
        if self.state not in ['BOUND_RX', 'BOUND_TRX']:
            log.err('WARNING: Received deliver_sm in wrong state: %s' % (
                self.state))
            return
        
        if pdu['header']['command_status'] != 'ESME_ROK':
            return
        
        # TODO: Only ACK messages once we've processed them?
        sequence_number = pdu['header']['sequence_number']
        pdu_resp = DeliverSMResp(sequence_number, **self.defaults)
        yield self.send_pdu(pdu_resp)
        
        pdu_params = pdu['body']['mandatory_parameters']
        pdu_opts = unpacked_pdu_opts(pdu)
        
        # We might have a `message_payload` optional field to worry about.
        message_payload = pdu_opts.get('message_payload', None)
        if message_payload is not None:
            pdu_params['short_message'] = message_payload.decode('hex')
        
        delivery_report = self.config.delivery_report_re.search(
            pdu_params['short_message'] or '')
        
        yield self._handle_deliver_sm_sms(pdu_params)        
