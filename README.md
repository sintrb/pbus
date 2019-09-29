pbus
===============
A simple application layer event-bus lib, support redis/mqtt/rabbitmq.

Install
===============
```
 pip install pbus
```

Useage
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
```

> 2. Use with URI(recommend)
```Python
import pbus
bus = pbus.connect("redis://:password@127.0.0.1:6379/2")    # with db 2
# or
bus = pbus.connect("mqtt://username:password@127.0.0.1:1883")    #
# or 
bus = pbus.connect("amqp://username:password@127.0.0.1:5672/myexchange")    #  with "myexchange" exchange

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


[Click to view more information!](https://github.com/sintrb/pbus)