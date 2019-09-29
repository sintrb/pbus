from __future__ import print_function

if __name__ == '__main__':
    import pbus
    import time, argparse

    parser = argparse.ArgumentParser(add_help=True)

    parser.add_argument('-u', '--uri', default="redis://127.0.0.1", help='event bus uri, example: "redis://:password@127.0.0.1:6379/2" "mqtt://username:password@127.0.0.1:1883" "amqp://username:password@127.0.0.1:5672/myexchange" ', type=str)
    parser.add_argument('-c', '--channel', help='the channel to of bus', type=str, default='pbus')
    parser.add_argument('-d', '--data', help='the publish data(if run with producer.), default is "Hello World!"', type=str, default='Hello World!')
    parser.add_argument('-p', '--producer', help='run with producer', default=False, action="store_true")
    parser.add_argument('-t', '--time', help='the time to show status', type=int, default=5)
    args = parser.parse_args()
    print('connecting to bus %s ...' % args.uri)
    bus = pbus.connect(args.uri)
    print('connecte success!')
    channel = args.channel
    data = args.data
    timegap = args.time
    total = 0
    runing = True


    def puser():
        global total
        import random, time
        st = time.time()
        ct = 0
        name = random.choice(list(range(10)))
        print('will publish "%s" to %s' % (data, channel))
        mct = 0
        while True:
            bus.publish(channel, data)
            ct += 1
            total += 1
            tg = int(max(time.time() - st, 0.001) * 1000)
            if time.time() - st >= timegap:
                mct += 1
                print(mct, ':', ' count', ct, 'time: %sms' % tg, 'speed: %d/s' % int(ct * 1000 / tg), 'total', total)
                ct = 0
                st = time.time()
            if not runing:
                break


    def suber():
        global total
        print('subscribing to %s ...' % channel)
        ps = bus.subscriber(channel)
        print('subscribe success!')
        print('waiting data from %s' % channel)
        st = time.time()
        ct = 0
        mct = 0
        for p in ps.listen():
            if p != data:
                raise Exception(u'msg error: %s' % p)
            total += 1
            ct += 1
            tg = int(max(time.time() - st, 0.001) * 1000)
            if time.time() - st >= timegap:
                mct += 1
                print(mct, ':', ' count', ct, 'time: %sms' % tg, 'speed: %d/s' % int(ct * 1000 / tg), 'total', total)
                ct = 0
                st = time.time()
            if not runing:
                break


    def run():
        if args.producer:
            puser()
        else:
            suber()


    try:
        import threading

        th = threading.Thread(target=run)
        th.setDaemon(True)
        th.start()
        while runing:
            time.sleep(1)
    except KeyboardInterrupt:
        print('will stop...')
        runing = False
        ct = 3
        while ct:
            print(ct, 's')
            time.sleep(1)
            ct -= 1
        print('total', total)
        exit(0)
