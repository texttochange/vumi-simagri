from twisted.trial.unittest import TestCase

from middlewares.content_encoding_middleware import ContentEncodingMiddleware

def mk_msg(content='unknown'):
    return {
        'content': content,
    }

class ContentEncodingMiddlewareTestCase(TestCase):
    
    def setUp(self):
        dummy_worker = object()
        self.mw = ContentEncodingMiddleware('mw', {}, dummy_worker)
        self.mw.setup_middleware()

    def test_handle_outbound(self):
        msg = mk_msg(content=u'Tamoin NAMA contact:+22678906255 Veut vendre 400 tonne Ma\xefs Blanc \xe0 135\xa0000 / tonne, Total HT 54\xa0000\xa0000 contact:+22678906255 l\'offre expire dans 10 jrs')
        msg = self.mw.handle_outbound(msg , 'dummy_endpoint')
        self.assertEqual(msg['content'],
            'Tamoin NAMA contact:+22678906255 Veut vendre 400 tonne Mais Blanc a 135 000 / tonne, Total HT 54 000 000 contact:+22678906255 l\'offre expire dans 10 jrs')        