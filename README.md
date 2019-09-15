pbus
===============
A simple application layer event-bus lib.

Install
===============
```
 pip install pbus
```

Useage
===============
> 1. Use with Redis

Subscriber

```python
import pbus
bus = pbus.RedisBus(host='127.0.0.1')
ps = bus.subscriber('test')
for data in ps.listen():
    print(data)
```

Publish
```Python
import pbus
bus = pbus.RedisBus(host='127.0.0.1')
bus.publish('test', 'Hello')
```

[Click to view more information!]('https://github.com/sintrb/pbus')