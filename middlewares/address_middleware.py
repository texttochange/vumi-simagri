import re

from vumi.middleware import BaseMiddleware
from vumi.log import log


class AddressMiddleware(BaseMiddleware):
    
    regex_plus = re.compile("^\+")
    regex_zeros = re.compile("^00")
    rules = {}
    
    def _setup_rule(self, config, addr):
        addr_rule = self.config.get(addr, {})
        rule = {
            'plus_outbound': addr_rule.get('plus_outbound', None),
            'plus_inbound': addr_rule.get('plus_inbound', None),
        }
        return rule
    
    def setup_middleware(self):
        self.rules['from_addr'] = self._setup_rule(self.config, 'from_addr')
        self.rules['to_addr'] = self._setup_rule(self.config, 'to_addr')
    
    def _apply_rule_plus(self, rule, addr):
        if rule == 'trim':
            return re.sub(self.regex_plus, "", addr)
        elif rule == 'ensure':
            if (not re.match(self.regex_plus, addr)):
                return '+%s' % addr
        return addr
    
    def handle_inbound(self, msg, endpoint):    
        msg['from_addr'] = self._apply_rule_plus(
            self.rules['from_addr']['plus_inbound'],
            msg['from_addr'])
        msg['to_addr'] = self._apply_rule_plus(
            self.rules['to_addr']['plus_inbound'],
            msg['to_addr'])
        return msg
    
    def handle_outbound(self, msg, endpoint):
        msg['from_addr'] = self._apply_rule_plus(
            self.rules['from_addr']['plus_outbound'],
            msg['from_addr'])
        msg['to_addr'] = self._apply_rule_plus(
            self.rules['to_addr']['plus_outbound'],
            msg['to_addr'])
        return msg
