from __future__ import print_function

try:
    import simplejson as json
except:
    import json


def encode_data(data):
    return json.dumps(data)


def decode_data(text):
    return json.loads(text)


class BasePubSub(object):
    def close(self):
        '''close PubSub'''
        pass

    def listen(self):
        '''start to listen data, return '''
        pass


class BaseBus(object):
    def publish(self, channel, data):
        '''publish data to channel'''
        pass

    def subscriber(self, channel):
        '''subscribe to channel, return a BasePubSub instance'''
        pass

    def subscriber_with_handler(self, channel, handler):
        '''subscribe to channel with handle function, return a BasePubSub instance.
        by default, it will create a thread to read message in a loop.
        '''
        import threading
        ps = self.subscriber(channel)

        def run():
            for m in ps.listen():
                handler(m)

        th = threading.Thread(target=run)
        th.setDaemon(True)
        th.start()
        return ps


class RedisBus(BaseBus):
    class RedisPubSub(BasePubSub):
        def __init__(self, ps):
            self.ps = ps

        def listen(self):
            listen = self.ps.listen()
            while self.ps.subscribed:
                res = next(listen)
                if not res or res.get('type') != 'message':
                    continue
                try:
                    data = decode_data(res['data'])
                except:
                    import traceback
                    traceback.print_exc()
                    continue
                yield data

        def close(self):
            self.ps.close()

    def __init__(self, host='127.0.0.1', port=6379, password=None, channel_prefix=None):
        import redis
        self.host = host
        self.port = port
        self.password = password
        self.channel_prefix = channel_prefix
        self.conn = redis.Redis(host=self.host, port=self.port, password=self.password)

    def _get_ful_channel(self, channel):
        return '%s%s' % (self.channel_prefix or '', channel)

    def publish(self, channel, data):
        self.conn.publish(self._get_ful_channel(channel), encode_data(data))

    def subscriber(self, channel):
        ps = self.conn.pubsub()
        ps.subscribe(self._get_ful_channel(channel))
        pps = RedisBus.RedisPubSub(ps)
        return pps
