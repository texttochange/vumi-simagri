import re

from vumi.log import log
from vumi.dispatchers import SimpleDispatchRouter


class TranportToTransportToAddrMultiplexRouter(SimpleDispatchRouter):
    
    def setup_routing(self):
        self.toaddr_mappings = []
        for name, toaddr_patterns in self.config['toaddr_mappings'].items():
            for toaddr_pattern in toaddr_patterns:
                toaddr_regex = '^%s%s' % (self.config['country_code'], toaddr_pattern)
                self.toaddr_mappings.append((name, re.compile(toaddr_regex)))
    
    #Route all message to exposed name
    def dispatch_inbound_message(self, msg):
        log.msg("Dispatch inbound %r" % msg)
        route_mapping = False
        try:
            names = self.config['route_mappings'][msg['transport_name']]
            for name in names:
                log.msg("Dispatch inbound to %s" % name)
                self.dispatcher.publish_outbound_message(name, msg.copy())
                route_mapping = True
        except:
            pass
        if route_mapping:
            return
        toaddr = msg['to_addr']
        for name, regex in self.toaddr_mappings:
            if regex.match(toaddr):
                log.msg("Dispatch outbound %s to %s" % (toaddr, name))
                self.dispatcher.publish_outbound_message(name, msg.copy())
                return
        if 'toaddr_fallback' in self.config and self.config['toaddr_fallback'] is not None:
            log.msg("Dispatch outbound %s to fallback" % toaddr)
            self.dispatcher.publish_outbound_message(self.config['toaddr_fallback'], msg.copy())
            return
        log.err("No route for %s" % repr(msg))

    #Do nothing as transport don't care about event
    def dispatch_inbound_event(self, msg):
        pass

    #Route the message according to to_addr
    def dispatch_outbound_message(self, msg):
        log.err("No route for outbound %s" % repr(msg))

