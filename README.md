pbus
===============
A simple application layer event-bus lib, support redis/mqtt/rabbitmq.

Install
===============
```
 pip install pbus
```

Usage
===============
> 1. Use with Redis/MQTT/RabbitMQ Bus class.

Subscriber

```python
import pbus
bus = pbus.RedisBus(host='127.0.0.1')   # need "pip install redis"
# or
bus = pbus.MQTTBus(host='127.0.0.1')   # need "pip install paho-mqtt"
# or
bus = pbus.RabbitMQBus(host='127.0.0.1')   # need "pip install pika"
# or
bus = pbus.MemoryBus(exchange='ex1')    # with memory, can't use in multi-processing
# or
bus = pbus.KafkaBus(host='127.0.0.1') # with kafa, need "pip install kafka"
ps = bus.subscriber('test')
for data in ps.listen():
    print(data)
```

Publish
```Python
import pbus
bus = pbus.RedisBus(host='127.0.0.1')
# or
bus = pbus.MQTTBus(host='127.0.0.1')
# or
bus = pbus.RabbitMQBus(host='127.0.0.1')
bus.publish('test', 'Hello')

bus = pbus.MemoryBus(exchange='ex1')
bus.publish('test', 'Hello')
```

> 2. Use with URI(recommend)
```Python
import pbus
bus = pbus.connect("redis://:password@127.0.0.1:6379/2")    # with db 2
# or
bus = pbus.connect("mqtt://username:password@127.0.0.1:1883")    #
# or 
bus = pbus.connect("amqp://username:password@127.0.0.1:5672/myexchange")    #  with "myexchange" exchange
# or
bus = pbus.connect("memory:/ex1")    #  with "test" exchange

# ...... other code

```

> 3. Test event-bus speed.
- a. Run consumer client
```bash
python -m pbus -u redis://127.0.0.1
```

- b. Run producer client
```bash
python -m pbus -u redis://127.0.0.1 -p
```

You will see:
```
connecting to bus redis://127.0.0.1 ...
connecte success!
subscribing to pbus ...
subscribe success!
waiting data from pbus
1 :  count 27748 time: 5000ms speed: 5549/s total 27748
2 :  count 83135 time: 5000ms speed: 16627/s total 110883
3 :  count 86416 time: 5000ms speed: 17283/s total 197299
4 :  count 72546 time: 5000ms speed: 14509/s total 269845
```

Ctrl+C to stop test.

- c. Run both consumer and producer
```bash
python -m pbus -u redis://127.0.0.1 -l
```

You will see:
```
Consumer: connecting to bus redis://127.0.0.1 ...
Consumer: connecte success!
Consumer: subscribing to pbus ...
Consumer: subscribe success!
Consumer: waiting data from pbus
Producer: connecting to bus redis://127.0.0.1 ...
Producer: connecte success!
Producer: will publish "Hello World!" to pbus
--Press Ctrl+C to stop it!--
Consumer: 1 :  count 29119 time: 5000ms speed: 5823/s total 29119
Producer: 1 :  count 29642 time: 5000ms speed: 5928/s total 29642
```


[Click to view more information!](https://github.com/sintrb/pbus)