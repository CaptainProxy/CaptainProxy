import BaseHTTPServer
import SimpleHTTPServer
import ssl
import select
import socket

'''
iptables -t nat -A PREROUTING -i br0 -s ! 192.168.0.4 -p tcp -d 208.71.186.86 --dport 443 -j DNAT --to 192.168.0.4:443
iptables -t nat -A POSTROUTING -o br0 -s 192.168.0.0/8 -d 192.168.0.4 -j SNAT --to 192.168.0.1
iptables -A FORWARD -s 192.168.0.0/8 -d 192.168.0.4 -i br0 -o eth0 -p tcp --dport 443 -j ACCEPT
'''

class DummyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    __base = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle = __base.handle
    server_version = 'Awesome/1.0'
    rbufsize = 0
    def do_GET(self):
        print 'Request from %s:%s' % self.client_address
        print '%s %s' % (self.command, self.path)
        for h in self.headers.headers:
            print h.strip()
        print
        self.connection.send('HTTP/1.0 200 OK\r\n')
        self.connection.send('nginx/1.2.1\r\n')
        self.connection.send('Content-Type: application/xml; charset=utf-8\r\n')
        self.connection.send('\r\n')
        self.connection.send(open('item_list.patched.xml', 'r').read())
        self.connection.close()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(('iap.gameloft.com', 0))
    ipaddr = sock.getsockname()[0]
    print '''Your computer's IP address is %s''' % ipaddr
    gw = raw_input('''Enter the IP address of the default gateway: (typically 192.168.0.1 or 192.168.1.1: ''')
    subnet = raw_input('''Enter your local subnet in CIDR notation (typically 192.168.0.0/8 or 192.168.1.0/8): ''')
    print '''Next, SSH into your router and run ifconfig to enumerate its networking interfaces. Then, answer the following questions.'''
    phone_if = raw_input('''Enter the name of the wifi interface on the router that your phone is connected to (i.e. wlan0, br0): ''')
    computer_if = raw_input('''Enter the name of the interface on the router that your computer is connected to (i.e. eth0, eth1, wlan0, br0): ''')
    print '''Run the following three commands on your router'''
    print '''iptables -t nat -A PREROUTING -i %s -s ! %s -p tcp -d 208.71.186.86 --dport 443 -j DNAT --to %s:443''' % (phone_if, ipaddr, ipaddr)
    print '''iptables -t nat -A POSTROUTING -o %s -s %s -d %s -j SNAT --to %s''' % (phone_if, subnet, ipaddr, gw)
    print '''iptables -A FORWARD -s %s -d %s -i %s -o %s -p tcp --dport 443 -j ACCEPT''' % (subnet, ipaddr, phone_if, computer_if)

    httpd = BaseHTTPServer.HTTPServer((ipaddr, 443), DummyHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='derpselfsignedcacert.pem', keyfile='selfsignedprivkey.pem', server_side=True)
    print '''The server is now running'''
    print
    httpd.serve_forever()

if __name__ == '__main__':
    main()
