__doc__ = """Tiny HTTP Proxy.

This module implements GET, HEAD, POST, PUT and DELETE methods
on BaseHTTPServer, and behaves as an HTTP proxy.  The CONNECT
method is also implemented experimentally, but has not been
tested yet.

Any help will be greatly appreciated.		SUZUKI Hisao
"""

__version__ = "0.2.1"

import BaseHTTPServer, select, socket, SocketServer, urlparse, xml.dom.minidom, time, socket

global intercept_original
intercept_original = ''
intercept_timestamp = 0

def patch_response(response):
    header = intercept_original[:intercept_original.find('\r\n\r\n')]
    body = intercept_original[intercept_original.find('\r\n\r\n')+4:]
    header_lines = header.split('\r\n')
    body = patch_prices(body)
    for i in range(len(header_lines)):
        if header_lines[i].find('Content-Length:') != -1:
            header_lines[i] = 'Content-Length: %d' % len(body)
    header = '\r\n'.join(header_lines)
    output = header + '\r\n\r\n' + body
    return output

def patch_prices(orig):
    dom = xml.dom.minidom.parseString(orig)
    for item in dom.getElementsByTagName('item'):
        price_types = item.getElementsByTagName('price_type')
        if len(price_types) != 1: continue
        price_type = price_types[0].firstChild.nodeValue
        if price_type == 'key':
            price_types[0].firstChild.nodeValue = 'coin'
        if price_type == 'cash' or price_type == 'social':
            price_types[0].firstChild.nodeValue = 'coin'
            price_values = item.getElementsByTagName('price_value')
            if len(price_values) != 1: continue
            textNode = price_values[0].firstChild
            textNode.nodeValue = str(100 * int(textNode.nodeValue))
    return dom.toxml('utf-8')

class ProxyHandler (BaseHTTPServer.BaseHTTPRequestHandler):
    __base = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle = __base.handle

    server_version = "TinyHTTPProxy/" + __version__
    rbufsize = 0                        # self.rfile Be unbuffered

    intercept = False

    def handle(self):
        (ip, port) =  self.client_address
        if hasattr(self, 'allowed_clients') and ip not in self.allowed_clients:
            self.raw_requestline = self.rfile.readline()
            if self.parse_request(): self.send_error(403)
        else:
            self.__base_handle()

    def _connect_to(self, netloc, soc):
        i = netloc.find(':')
        if i >= 0:
            host_port = netloc[:i], int(netloc[i+1:])
        else:
            host_port = netloc, 80
        print "\t" "connect to %s:%d" % host_port
        try: soc.connect(host_port)
        except socket.error, arg:
            try: msg = arg[1]
            except: msg = arg
            self.send_error(404, msg)
            return 0
        return 1

    def do_CONNECT(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if self._connect_to(self.path, soc):
                self.log_request(200)
                self.wfile.write(self.protocol_version +
                                 " 200 Connection established\r\n")
                self.wfile.write("Proxy-agent: %s\r\n" % self.version_string())
                self.wfile.write("\r\n")
                self._read_write(soc, 300)
        finally:
            print "\t" "bye"
            soc.close()
            self.connection.close()

    def do_GET(self):
        global intercept_original, intercept_timestamp
        if time.time() > (intercept_timestamp + 3600):
            intercept_original = ''
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse(
            self.path, 'http')
        netloc = '208.71.186.73'
        if path == '/partners/offline_ingame/item_list.php' and (query == 'platform=android&product=1370' or query == 'product=1370'):
            self.intercept = True
        if scm != 'http' or fragment or not netloc:
            self.send_error(400, "bad url %s" % self.path)
            return
        if self.intercept and intercept_original:
            try:
                self.connection.send(patch_response(intercept_original))
                self._read()
            finally:
                print "\t" "cached response"
                self.connection.close()
        else:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                if self._connect_to(netloc, soc):
                    self.log_request()
                    soc.send("%s %s %s\r\n" % (
                        self.command,
                        urlparse.urlunparse(('', '', path, params, query, '')),
                        self.request_version))
                    self.headers['Connection'] = 'close'
                    del self.headers['Proxy-Connection']
                    for key_val in self.headers.items():
                        soc.send("%s: %s\r\n" % key_val)
                    soc.send("\r\n")
                    self._read_write(soc)
            finally:
                print "\t" "bye"
                soc.close()
                self.connection.close()

    def _read(self, max_idling=20):
        iw = [self.connection]
        ow = []
        count = 0
        while 1:
            count += 1
            (ins, _, exs) = select.select(iw, ow, iw, 3)
            if exs: break
            if ins:
                for i in ins:
                    data = i.recv(8192)
                    if data:
                        count = 0
            else:
                print "\t" "idle", count
            if count == max_idling: break

    def _read_write(self, soc, max_idling=20):
        global intercept_original, intercept_timestamp
        iw = [self.connection, soc]
        ow = []
        count = 0
        buf = ''
        while 1:
            count += 1
            (ins, _, exs) = select.select(iw, ow, iw, 3)
            if exs: break
            if ins:
                for i in ins:
                    if i is soc:
                        out = self.connection
                    else:
                        out = soc
                    data = i.recv(8192)
                    if self.intercept and i == soc and data:
                        buf = buf + data
                        count = 0
                    elif data:
                        out.send(data)
                        count = 0
            else:
                print "\t" "idle", count
            if count == max_idling: break
        if self.intercept:
            intercept_timestamp = time.time()
            intercept_original = buf
            self.connection.send(patch_response(intercept_original))

    do_HEAD = do_GET
    do_POST = do_GET
    do_PUT  = do_GET
    do_DELETE=do_GET

class ThreadingHTTPServer (SocketServer.ThreadingMixIn,
                           BaseHTTPServer.HTTPServer): pass

if __name__ == '__main__':
    from sys import argv 
    if argv[1:] and argv[1] in ('-h', '--help'):
        print argv[0], "[port [allowed_client_name ...]]"
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('confirmation.gameloft.com', 0))
        ipaddr = sock.getsockname()[0]
        print '''Your computer's IP address is %s''' % ipaddr
        gw = raw_input('''Enter the IP address of the default gateway: (typically 192.168.0.1 or 192.168.1.1: ''')
        subnet = raw_input('''Enter your local subnet in CIDR notation (typically 192.168.0.0/8 or 192.168.1.0/8): ''')
        print '''Next, SSH into your router and run ifconfig to enumerate its networking interfaces. Then, answer the following questions.'''
        phone_if = raw_input('''Enter the name of the wifi interface on the router that your phone is connected to (i.e. wlan0, br0): ''')
        computer_if = raw_input('''Enter the name of the interface on the router that your computer is connected to (i.e. eth0, eth1, wlan0, br0): ''')
        print '''Run the following three commands on your router'''
        print '''iptables -t nat -A PREROUTING -i %s -s ! %s -p tcp -d 208.71.186.73 --dport 80 -j DNAT --to %s:80''' % (phone_if, ipaddr, ipaddr)
        print '''iptables -t nat -A POSTROUTING -o %s -s %s -d %s -j SNAT --to %s''' % (phone_if, subnet, ipaddr, gw)
        print '''iptables -A FORWARD -s %s -d %s -i %s -o %s -p tcp --dport 80 -j ACCEPT''' % (subnet, ipaddr, phone_if, computer_if)

        print "Any clients will be served..."
        ProxyHandler.protocol_version = 'HTTP/1.0'
        httpd = ThreadingHTTPServer((ipaddr, 80), ProxyHandler)
        httpd.serve_forever()
