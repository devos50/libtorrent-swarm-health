import math
import sys

import libtorrent as lt
from libtorrent import bdecode

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

session = lt.session()
session.set_alert_mask(lt.alert.category_t.dht_log_notification)


class SwarmHealthManager(object):

    def __init__(self):
        self.infohash = None
        self.bloomfilters = []  # List of tuples of seeders/peers bloomfilters

    def process_alerts(self):
        for alert in session.pop_alerts():
            if alert.category() & lt.alert.category_t.dht_log_notification:
                if alert.__class__.__name__ == "dht_pkt_alert":
                    decoded = bdecode(alert.pkt_buf)
                    if 'r' in decoded:
                        if 'BFsd' in decoded['r'] and 'BFpe' in decoded['r']:
                            self.bloomfilters.append((bytearray(decoded['r']['BFsd']), bytearray(decoded['r']['BFpe'])))

    def get_bloomfilter_size(self, bloomfilter):
        def tobits(s):
            result = []
            for c in s:
                bits = bin(ord(c))[2:]
                bits = '00000000'[len(bits):] + bits
                result.extend([int(b) for b in bits])
            return result

        bits_array = tobits(str(bloomfilter))
        total_zeros = 0
        for bit in bits_array:
            if bit == 0:
                total_zeros += 1

        if total_zeros == 0:
            return 6000  # The maximum capacity of the bloom filter used

        m = 256 * 8
        c = min(m - 1, total_zeros)
        return math.log(c / float(m)) / (2 * math.log(1 - 1 / float(m)))

    def determine_health(self):
        final_bfsd = bytearray(256)
        final_bfpe = bytearray(256)

        # Combine filters
        for bfsd, bfpe in self.bloomfilters:
            for i in range(len(final_bfsd)):
                final_bfsd[i] = final_bfsd[i] | bfsd[i]
                final_bfpe[i] = final_bfpe[i] | bfpe[i]

        print "seeders: %d" % self.get_bloomfilter_size(final_bfsd)
        print "leechers: %d" % self.get_bloomfilter_size(final_bfpe)
        reactor.stop()

    def do_dht_lookup(self):
        session.dht_get_peers(self.infohash)

    def start(self, infohash):
        self.infohash = infohash
        lc = LoopingCall(self.process_alerts)
        lc.start(2)

        session.add_dht_router('router.bittorrent.com', 6881)
        session.add_dht_router('router.utorrent.com', 6881)
        session.add_dht_router('router.bitcomet.com', 6881)
        session.start_dht()

        reactor.callLater(10, self.do_dht_lookup)
        reactor.callLater(20, self.determine_health)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "You should provide an infohash!"
        exit(1)

    print "Will check DHT health of infohash %s" % sys.argv[1]
    infohash = sys.argv[1].decode('hex')
    sha1_infohash = lt.sha1_hash(infohash)

    swarm_health_manager = SwarmHealthManager()
    reactor.callWhenRunning(swarm_health_manager.start, sha1_infohash)
    reactor.run()
