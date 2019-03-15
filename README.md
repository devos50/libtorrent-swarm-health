# Libtorrent swarm health estimator

This simple command line tool can be used to estimate the swarm size (number of seeders and leechers) of a libtorrent swarm. This is helpful in the situation where tracker information is not always available. It relies on [the BEP33 extension](http://www.bittorrent.org/beps/bep_0033.html).

This tool is built with Python 2.7 and the Twisted networking library. It also depends on a modified version of libtorrent 1.2.0 since BEP33 requests are not performed by default by the libtorrent core. In addition, one has to expose several methods in the libtorrent Python bindings to receive and parse the BEP33 bloom filters. The exact changes can be found on [my libtorrent fork](https://github.com/devos50/libtorrent/tree/bep33_support).

The check itself takes around 20 seconds. In the first 10 seconds, your node is being bootstrapped in the Kademlia DHT. After that, we send a `get_peers` request to other peers with the infohash provided to the application (see below). During a period of 10 seconds, we accumulate bloomfilters we receive in the `get_peers` responses and combine them afterwards. This allows us to estimate the number of seeders and leechers in a swarm, without relying on a centralized tracker.

### Usage

```
python check_dht_health.py <YOUR HEX-ENCODED INFOHASH>
```

This should result the following output:

```
Will check DHT health of infohash <YOUR HEX-ENCODED INFOHASH>
seeders: 36
leechers: 27
```