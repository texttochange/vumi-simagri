
from twisted.internet.defer import inlineCallbacks
from smpp.pdu_builder import PDU

from vumi.transports.smpp.clientserver.client import unpacked_pdu_opts
from vumi.transports.smpp.clientserver.client import EsmeTransceiver, EsmeTransceiverFactory
from vumi.transports.smpp import SmppTransport

from vumi import log


class TelecelBfSmppTransport(SmppTransport):

    def make_factory(self):
        return EsmeDataTransceiverFactory(
            self.client_config,
            self.redis,
            self.esme_callbacks)


class EsmeDataTransceiverFactory(EsmeTransceiverFactory):

    def buildProtocol(self, addr):
        log.msg('Connected')
        self.esme = EsmeDataTransceiver(
            self.config, self.redis, self.esme_callbacks)
        self.resetDelay()
        return self.esme


class EsmeDataTransceiver(EsmeTransceiver):

    @inlineCallbacks
    def handle_data_sm(self, pdu):
        if self.state not in ['BOUND_RX', 'BOUND_TRX']:
            log.err('WARNING: Received deliver_sm in wrong state: %s' % (
                self.state))
            return
        
        if pdu['header']['command_status'] != 'ESME_ROK':
            return
        
        # TODO: Only ACK messages once we've processed them?
        sequence_number = pdu['header']['sequence_number']
        pdu_resp = DataSMResp(sequence_number, **self.defaults)
        yield self.send_pdu(pdu_resp)
        
        pdu_params = pdu['body']['mandatory_parameters']
        pdu_opts = unpacked_pdu_opts(pdu)
        
        # We might have a `message_payload` optional field to worry about.
        message_payload = pdu_opts.get('message_payload', None)
        if message_payload is not None:
            pdu_params['short_message'] = message_payload.decode('hex')
        
        delivery_report = self.config.delivery_report_re.search(
            pdu_params['short_message'] or '')
        
        esm_class = pdu['body']['mandatory_parameters']['esm_class']
        if not esm_class is 0:
            log.err('WARNING: Received data_sm with esm_class: %s' % (
                esm_class))
            return
        
        yield self._handle_deliver_sm_sms(pdu_params)


class DataSMResp(PDU):
    def __init__(self,
            sequence_number,
            message_id = '',
            command_status = 'ESME_ROK',
            **kwargs):
        super(DataSMResp, self).__init__(
                'data_sm_resp',
                command_status,
                sequence_number,
                **kwargs)
        self.obj['body'] = {}
        self.obj['body']['mandatory_parameters'] = {}
        self.obj['body']['mandatory_parameters']['message_id'] = ''
