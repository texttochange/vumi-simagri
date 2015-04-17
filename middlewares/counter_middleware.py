import redis

from vumi.middleware import BaseMiddleware
from vumi.log import log


class CounterMiddleware(BaseMiddleware):

    def setup_middleware(self):
        self.r_server = redis.Redis()
        self.op_name = self.config.get('op_name', 'nooperator')

    def handle_outbound(self, msg, endpoint):
        compteur =self.r_server.incr("%s:outbound_msg_counter" % self.op_name)       
        log.msg("OUTBOUND_MSG_TOTAL %s" % compteur )        
        return msg
    
    def handle_inbound(self, msg, endpoint):
        self.r_server.incr("%s:inbound_msg_counter" % self.op_name)
        return msg    
