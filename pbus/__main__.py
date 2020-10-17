from __future__ import print_function

if __name__ == '__main__':
    import pbus
    import time, argparse
    from threading import Condition

    try:
        from Queue import Queue, Empty
    except:
        from queue import Queue, Empty
    parser = argparse.ArgumentParser(add_help=True)

    parser.add_argument('-u', '--uri', default="redis://127.0.0.1", help='event bus uri, example: "redis://:password@127.0.0.1:6379/2" "mqtt://username:password@127.0.0.1:1883" "amqp://username:password@127.0.0.1:5672/myexchange" ', type=str)
    parser.add_argument('-c', '--channel', help='the channel to of bus', type=str, default='pbus')
    parser.add_argument('-d', '--data', help='the publish data(if run with producer.), default is "Hello World!"', type=str, default='Hello World!')
    parser.add_argument('-p', '--producer', help='run with producer', default=False, action="store_true")
    parser.add_argument('-t', '--time', help='the time to show status', type=int, default=5)
    parser.add_argument('-l', '--loop', help='auto send and receive', default=False, action="store_true")
    args = parser.parse_args()
    channel = args.channel
    data = args.data
    timegap = args.time
    p_total = 0
    c_total = 0
    runing = True
    stoped = False

    print_queue = Queue()
    cond = Condition()


    def print_thread():
        while not stoped:
            try:
                txt = print_queue.get(timeout=1)
                print(txt)
            except Empty:
                pass


    def print_it(*args):
        print_queue.put(' '.join(map(str, args)))


    def wait():
        with cond:
            cond.wait()


    def notify():
        with cond:
            cond.notifyAll()


    def puser():
        global p_total
        TAG = 'Producer:'
        print_it(TAG, 'connecting to bus %s ...' % args.uri)
        bus = pbus.connect(args.uri)
        print_it(TAG, 'connecte success!')
        print_it(TAG, 'will publish "%s" to %s' % (data, channel))

        ct = 0
        mct = 0
        time.sleep(.1)
        notify()
        st = time.time()
        while True:
            bus.publish(channel, data)
            ct += 1
            p_total += 1
            tg = int(max(time.time() - st, 0.001) * 1000)
            if time.time() - st >= timegap or not runing:
                mct += 1
                print_it(TAG, mct, ':', ' count', ct, 'time: %sms' % tg, 'speed: %d/s' % int(ct * 1000 / tg), 'total', p_total)
                ct = 0
                st = time.time()
            if not runing:
                break


    def suber():
        global c_total
        TAG = 'Consumer:'
        print_it(TAG, 'connecting to bus %s ...' % args.uri)
        bus = pbus.connect(args.uri)
        print_it(TAG, 'connecte success!')
        print_it(TAG, 'subscribing to %s ...' % channel)
        ps = bus.subscriber(channel)
        print_it(TAG, 'subscribe success!')
        print_it(TAG, 'waiting data from %s' % channel)
        ct = 0
        mct = 0
        time.sleep(.1)
        notify()
        st = time.time()
        for p in ps.listen():
            if p != data:
                raise Exception(u'msg error: %s' % p)
            c_total += 1
            ct += 1
            tg = int(max(time.time() - st, 0.001) * 1000)
            if time.time() - st >= timegap or not runing:
                mct += 1
                print_it(TAG, mct, ':', ' count', ct, 'time: %sms' % tg, 'speed: %d/s' % int(ct * 1000 / tg), 'total', c_total)
                ct = 0
                st = time.time()
            if not runing:
                break


    def start_thread(target):
        import threading
        def th():
            try:
                target()
            except:
                global runing
                import traceback
                traceback.print_exc()
                time.sleep(.1)
                notify()
                time.sleep(.1)
                stop()
                time.sleep(.1)
                notify()

        th = threading.Thread(target=th)
        th.setDaemon(True)
        th.start()


    start_thread(print_thread)


    def run():
        if args.loop:
            start_thread(suber)
            wait()
            start_thread(puser)
        elif args.producer:
            puser()
        else:
            suber()
        wait()
        print_it('--Press Ctrl+C to stop it!--')


    def stop():
        global runing, stoped
        print_it('will stop...')
        runing = False
        ct = 3
        while ct:
            print_it(ct, 's')
            time.sleep(1)
            ct -= 1
        if args.loop:
            print_it('p_total', p_total, 'c_total', c_total, 'total', p_total + c_total)
        elif args.producer:
            print_it('p_total', p_total)
        else:
            print_it('c_total', c_total)
        time.sleep(.1)
        stoped = True
        exit(0)


    try:
        start_thread(run)
        while runing:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
