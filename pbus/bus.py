from __future__ import print_function

try:
    import simplejson as json
except:
    import json


def encode_data(data):
    return json.dumps(data)


def decode_data(text):
    return json.loads(text)


LOCALHOST = "localhost"


class BasePubSub(object):
    def close(self):
        '''close PubSub'''
        pass

    def listen(self):
        '''start to listen data, return '''
        pass


class Lock(object):
    def __init__(self, name='default'):
        from threading import Lock
        self.name = name
        self.lock = Lock()

    def __enter__(self):
        # print('locking', self.name)
        self.lock.acquire()
        # print('locked', self.name)

    def __exit__(self, *unused):
        self.lock.release()
        # print('released', self.name)


class FuncBus(object):
    _func_map = {}
    _runing = False

    def __init__(self, bus, channel):
        self.bus = bus
        self.channel = channel

    def _run(self):
        self._runing = True
        while self._runing:
            for d in self.bus.subscriber(self.channel).listen():
                if not d or not d.get('fkey'):
                    continue
                fkey = d['fkey']
                if fkey not in self._func_map:
                    print(fkey, 'not in self._func_map')
                # print(os.getpid(), 'run ', fkey, d)
                args = d['args']
                kwargs = d['kwargs']
                self._func_map[fkey](*args, **kwargs)

    def start(self):
        import threading
        th = threading.Thread(target=self._run)
        th.setDaemon(True)
        th.start()
        return th

    def register(self, func):
        import functools
        functools.wraps(func)
        fkey = func.__name__
        if fkey in self._func_map:
            raise Exception('%s registered', func)
        self._func_map[fkey] = func
        if not self._runing:
            self.start()

        def _func(*args, **kwargs):
            d = {'fkey': fkey, 'args': args, 'kwargs': kwargs}
            # print(os.getpid(), 'call', fkey, d)
            self.bus.publish(self.channel, d)

        return _func


class BaseBus(object):
    channel_prefix = ''
    lock = Lock()
    _func_bus_map = {}

    def _get_ful_channel(self, channel):
        return '%s%s' % (self.channel_prefix or '', channel)

    def publish(self, channel, data):
        '''publish data to channel'''
        pass

    def subscriber(self, channel):
        '''subscribe to channel, return a BasePubSub instance'''
        raise NotImplemented

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

    def _get_func_bus(self, channel):
        if channel not in self._func_bus_map:
            self._func_bus_map[channel] = FuncBus(bus=self, channel=channel)
        return self._func_bus_map[channel]

    def func_bus(self, func_or_channel=None):
        default = 'default'
        channel = default if callable(func_or_channel) else func_or_channel or default
        fbus = self._get_func_bus(channel)
        if callable(func_or_channel):
            return fbus.register(func_or_channel)
        else:
            return fbus


class RedisBus(BaseBus):
    class RedisPubSub(BasePubSub):
        def __init__(self, ps):
            self.ps = ps

        def listen(self):
            listen = self.ps.listen()
            while self.ps.subscribed:
                try:
                    res = next(listen)
                except:
                    pass
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

    def __init__(self, host=LOCALHOST, port=6379, password=None, channel_prefix=None, db=0):
        import redis
        self.host = host
        self.port = port
        self.password = password
        self.channel_prefix = channel_prefix
        self.db = db
        self.conn = redis.Redis(host=self.host, port=self.port, password=self.password, db=self.db)

    def publish(self, channel, data):
        self.conn.publish(self._get_ful_channel(channel), encode_data(data))

    def subscriber(self, channel):
        ps = self.conn.pubsub()
        ps.subscribe(self._get_ful_channel(channel))
        rps = RedisBus.RedisPubSub(ps)
        return rps


class MQTTBus(BaseBus):
    class MQTTPubSub(BasePubSub):
        def __init__(self, channel, bus, handler):
            try:
                from Queue import Queue
            except:
                from queue import Queue
            self.bus = bus
            self.channel = channel
            self.handler = handler
            self.queue = Queue()

        listened = False
        subscribed = True

        def listen(self):
            self.listened = True
            while self.listened:
                data = self.queue.get()
                yield data

        def close(self):
            self.listened = False
            self.subscribed = False

        def _handle_data(self, data):
            if self.handler:
                self.handler(data)
            elif self.listened:
                self.queue.put(data)

    connected = False
    subscriber_map = {}

    def __init__(self, host=LOCALHOST, port=1883, username=None, password=None, channel_prefix=None):
        import uuid
        from paho.mqtt.client import Client
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.channel_prefix = channel_prefix
        clientid = str(uuid.uuid4())
        self.mqttclient = Client(client_id=clientid)
        if self.username:
            self.mqttclient.username_pw_set(self.username, self.password or None)
        self.mqttclient.on_connect = self._on_connect
        self.mqttclient.on_message = self._on_message
        self._connect()

    def _connect(self):
        import threading
        if self.username:
            self.mqttclient.username_pw_set(self.username, self.password)
        self.mqttclient.connect(self.host, self.port)
        th = threading.Thread(target=self._forloop)
        th.setDaemon(True)
        th.start()

    def _disconnect(self):
        self.mqttclient.disconnect()

    def subscriber_with_handler(self, channel, handler):
        ful_channel = self._get_ful_channel(channel)
        with self.lock:
            if ful_channel not in self.subscriber_map:
                self.mqttclient.subscribe(topic=ful_channel)
                self.subscriber_map[ful_channel] = {
                    'mpss': [],
                }
            mps = MQTTBus.MQTTPubSub(channel, self, handler)
            self.subscriber_map[ful_channel]['mpss'].append(mps)
        return mps

    def subscriber(self, channel):
        return self.subscriber_with_handler(channel, None)

    def publish(self, channel, data):
        return self.mqttclient.publish(self._get_ful_channel(channel), payload=encode_data(data))

    def _forloop(self):
        self.mqttclient.loop_forever()

    def _on_connect(self, client, userdata, flags, rc):
        # print("_on_connect", client, userdata, flags, rc)
        self.connected = True

    def _on_message(self, client, userdata, msg):
        # print("_on_message", client, userdata, msg.topic, msg.payload)
        try:
            ful_channel = msg.topic
            data = decode_data(msg.payload.decode('utf-8'))
            if ful_channel in self.subscriber_map:
                changed = True
                for mps in self.subscriber_map[ful_channel]['mpss']:
                    if mps.subscribed:
                        mps._handle_data(data)
                    else:
                        changed = True
                if changed:
                    with self.lock:
                        mpss = filter(lambda mps: mps.subscribed, self.subscriber_map[ful_channel]['mpss'])
                        if not mpss:
                            self.mqttclient.unsubscribe(topic=ful_channel)
                            del self.subscriber_map[ful_channel]
                        else:
                            self.subscriber_map[ful_channel]['mpss'] = mpss

        except:
            import traceback
            traceback.print_exc()


class RabbitMQBus(BaseBus):
    class RabbitMQPubSub(BasePubSub):
        def __init__(self, queue_name, rbmqchannel):
            try:
                from Queue import Queue
            except:
                from queue import Queue
            self.queue_name = queue_name
            self.rbmqchannel = rbmqchannel
            self.queue = Queue()

        listened = False

        def listen(self):
            self.listened = True
            for method_frame, properties, body in self.rbmqchannel.consume(self.queue_name, auto_ack=True):
                if not self.listened:
                    break
                data = decode_data(body)
                yield data

        def close(self):
            self.listened = False
            self.rbmqchannel.queue_delete(self.queue_name)
            self.rbmqchannel.close()
            con = self.rbmqchannel.connection
            con.close()

    def __init__(self, host=LOCALHOST, port=5672, username=None, password=None, exchange=None, channel_prefix=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.exchange = exchange or 'pbus'
        self.channel_prefix = channel_prefix
        # self.rbmqcon = self.create_connection()

    def create_connection(self):
        import pika
        credentials = pika.PlainCredentials(self.username, self.password) if self.username else None
        rbmqcon = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials, heartbeat=0))
        return rbmqcon

    def create_channel(self):
        rbmqcon = self.create_connection()
        channel = rbmqcon.channel()
        if not self._exchange_declared:
            channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
            self._exchange_declared = True
        return channel

    def subscriber(self, channel):
        ful_channel = self._get_ful_channel(channel)
        rbmqchannel = self.create_channel()
        result = rbmqchannel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        # print('bind', self.exchange, queue_name, ful_channel)
        rbmqchannel.queue_bind(exchange=self.exchange, queue=queue_name, routing_key=ful_channel)
        rmqps = RabbitMQBus.RabbitMQPubSub(queue_name, rbmqchannel)
        return rmqps

    _pubchannel = None
    _exchange_declared = False

    def publish(self, channel, data):
        ful_channel = self._get_ful_channel(channel)
        if not self._pubchannel:
            self._pubchannel = self.create_channel()
        # print('pub', self.exchange, ful_channel)
        self._pubchannel.basic_publish(exchange=self.exchange,
                                       routing_key=ful_channel,
                                       body=encode_data(data))


class MemoryBus(BaseBus):
    class MemoryBusPubSub(BasePubSub):
        def __init__(self, bus, queue, ful_channel):
            self.bus = bus
            self.queue = queue
            self.ful_channel = ful_channel

        listened = False
        subscribed = True

        def listen(self):
            self.listened = True
            while self.listened:
                data = decode_data(self.queue.get())
                yield data

        def close(self):
            self.listened = False
            self.subscribed = False
            self.bus.del_pubsub(self)

    def add_pubsub(self, pubsub):
        ful_channel = pubsub.ful_channel
        if self.exchange not in MemoryBus._EXCHANGE_MAP:
            MemoryBus._EXCHANGE_MAP[self.exchange] = {}
        if ful_channel not in MemoryBus._EXCHANGE_MAP[self.exchange]:
            MemoryBus._EXCHANGE_MAP[self.exchange][ful_channel] = list()
        MemoryBus._EXCHANGE_MAP[self.exchange][ful_channel].append(pubsub)
        return len(MemoryBus._EXCHANGE_MAP[self.exchange][ful_channel])

    def del_pubsub(self, pubsub):
        if self.exchange in MemoryBus._EXCHANGE_MAP:
            ful_channel = pubsub.ful_channel
            if ful_channel in MemoryBus._EXCHANGE_MAP[self.exchange]:
                MemoryBus._EXCHANGE_MAP[self.exchange].remove(pubsub)
                return MemoryBus._EXCHANGE_MAP[self.exchange][ful_channel]
        return 0

    _EXCHANGE_MAP = {}

    def __init__(self, exchange=None, channel_prefix=None):
        self.exchange = exchange or 'pbus'
        self.channel_prefix = channel_prefix
        self.busid = str(id(self))

    def subscriber(self, channel):
        ful_channel = self._get_ful_channel(channel)
        try:
            from Queue import Queue
        except:
            from queue import Queue
        queue = Queue()
        pubsub = MemoryBus.MemoryBusPubSub(self, queue, ful_channel)
        self.add_pubsub(pubsub)
        return pubsub

    def publish(self, channel, data):
        ex = MemoryBus._EXCHANGE_MAP.get(self.exchange)
        if ex:
            for pubsub in ex.get(self._get_ful_channel(channel), []):
                pubsub.queue.put(encode_data(data))


class KafkaBus(BaseBus):
    class KafkaBusPubSub(BasePubSub):
        def __init__(self, bus, ful_channel):
            self.bus = bus
            self.ful_channel = ful_channel

        listened = False
        subscribed = True

        def listen(self):
            self.listened = True
            from kafka import KafkaConsumer
            cs = KafkaConsumer(self.ful_channel, bootstrap_servers=self.bus.bootstrap_servers, sasl_plain_username=self.bus.username, sasl_plain_password=self.bus.password)
            for v in cs:
                yield decode_data(v.value.decode('utf8'))
                if not self.listened:
                    break

        def close(self):
            self.listened = False
            self.subscribed = False

    def __init__(self, host=LOCALHOST, port=9092, username=None, password=None, partition=None, channel_prefix=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.partition = partition
        self.channel_prefix = channel_prefix
        self._kafka = None

    @property
    def bootstrap_servers(self):
        return '%s:%s' % (self.host, self.port)

    def subscriber(self, channel):
        ful_channel = self._get_ful_channel(channel)
        pubsub = KafkaBus.KafkaBusPubSub(self, ful_channel)
        return pubsub

    def publish(self, channel, data):
        if self._kafka == None:
            import kafka
            self._kafka = kafka.KafkaProducer(bootstrap_servers=self.bootstrap_servers, sasl_plain_username=self.username, sasl_plain_password=self.password)
        self._kafka.send(self._get_ful_channel(channel), value=encode_data(data).encode('utf8'), partition=self.partition)


def connect(uri):
    '''
    Connect to bus server with uri.
    :param uri: the bus server uri, example: mqtt://localhost:1883 , redis://user:secret@localhost:6379/0
    :return: Bus instance
    '''
    import re
    try:
        import urlparse as parse
    except:
        from urllib import parse
    res = parse.urlparse(uri)
    if res.scheme == 'redis':
        # redis
        db = 0
        rs = re.findall('^/(\d+)$', res.path or '')
        if rs:
            db = int(rs[0])
        bus = RedisBus(host=res.hostname or 'localhost', port=int(res.port or 6379), password=res.password or None, db=db)
    elif res.scheme == 'mqtt':
        # mqtt
        bus = MQTTBus(host=res.hostname or 'localhost', port=int(res.port or 1883), username=res.username or None, password=res.password or None)
    elif res.scheme == 'amqp':
        # rabbitmq
        bus = RabbitMQBus(host=res.hostname or 'localhost', port=int(res.port or 5672), username=res.username or None, password=res.password or None, exchange=(res.path or '').lstrip('/'))
    elif res.scheme == 'memory':
        # memory
        bus = MemoryBus(exchange=(res.path or '').lstrip('/') or 'default')
    elif res.scheme == 'kafka':
        # kafka
        bus = KafkaBus(host=res.hostname or 'localhost', port=int(res.port or 9092), username=res.username or None, password=res.password or None)
    else:
        raise Exception('Unknow uri: %s' % uri)
    return bus
