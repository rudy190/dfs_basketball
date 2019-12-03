from datetime import datetime
from queue import Queue
from datetime import timedelta
import time

class ProxyQueue():
    def __init__(self):
        self.timeout_pause = timedelta(minutes=5)
        self.pause_penalty = 5
        self.user = 'd6e048be13'
        self.pw = 'uVA25yqC'
        self.ips = ['149.20.244.254', '199.250.188.145', '199.250.189.116',
                   '23.244.230.130', '23.89.115.198', None]
        self.proxies = Queue(maxsize=6)
        self.init_proxies()

    def init_proxies(self):
        for ip in self.ips:
            proxy_address = self.get_proxy_address(ip)
            self.put_proxy(proxy_address)

    def get_proxy_address(self, ip):
        if ip is not None:
            proxy_address = {'http': 'http://{}:{}@{}/'.format(self.user, self.pw, ip)}
        else:
            proxy_address = None
        return proxy_address

    def put_proxy(self, proxy_address):
        self.proxies.put({'proxy_address':proxy_address,
                          'last_used_time':datetime.now(),
                          'timeout':False,
                          'pause_sec':self.get_proxy_pause_sec(proxy_address)})

    def timeout_proxy(self, proxy_address, last_used_time):
        self.proxies.put({'proxy_address':proxy_address,
                          'last_used_time':last_used_time,
                          'timeout':True,
                          'pause_sec':self.get_proxy_pause_sec(proxy_address)})

    def get_proxy_pause_sec(self, proxy_address):
        pause_sec = 0
        if proxy_address is None:
            pause_sec = self.pause_penalty
        return timedelta(seconds=pause_sec)

    def get_proxy(self):
        proxy = self.proxies.get()
        current_time = datetime.now()
        last_used_time = proxy['last_used_time']
        pause_sec = proxy['pause_sec']
        if proxy['timeout'] is False:
            self.pause_proxy_return(last_used_time, current_time, pause_sec)
        elif proxy['timeout'] is True:
            if self.timeout_status(last_used_time, current_time):
                self.timeout_proxy(proxy['proxy_address'], last_used_time)
                proxy = self.get_proxy()
        return proxy

    def timeout_status(self, last_used_time, current_time):
        if (current_time - last_used_time) < self.timeout_pause:
            return True
        else:
            return False

    def pause_proxy_return(self, last_used_time, current_time, pause_sec):
        if (current_time - last_used_time) < pause_sec:
            pause = (pause_sec - (current_time - last_used_time))
            sec_sleep = (pause.seconds + pause.microseconds / 1000000)
            time.sleep(sec_sleep)

    def set_pause_penalty(self, pause_penalty):
        self.pause_penalty = pause_penalty

Proxies = ProxyQueue()
