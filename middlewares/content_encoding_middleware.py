
from unidecode import unidecode
from vumi.middleware import BaseMiddleware


class ContentEncodingMiddleware(BaseMiddleware):

    def handle_outbound(self, msg, endpoint):
        msg['content'] = unidecode(msg['content'])
        return msg
