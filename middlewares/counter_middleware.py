import redis

from vumi.middleware import BaseMiddleware


class CounterMiddleware(BaseMiddleware):

    def setup_middleware(self):
        self.r_server = redis.Redis()
        self.op_name = self.config.get('op_name', 'nooperator')

    def handle_outbound(self, msg, endpoint):
        self.r_server.incr("%s:outbound_msg_counter" % self.op_name)
        return msg
    
    def handle_inbound(self, msg, endpoint):
        self.r_server.incr("%s:inbound_msg_counter" % self.op_name)
        return msg    
