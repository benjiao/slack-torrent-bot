import json
import transmissionrpc


class TorrentController:
    def __init__(self, config):
        self.tc = transmissionrpc.Client(
            address=config['transmission']['address'],
            port=config['transmission']['port'],
            user=config['transmission'].get('user', None),
            password=config['transmission'].get('password', None))

        self.torrent_session = self.tc.get_session()

    def get_torrents(self):
        results = self.tc.get_torrents()
        torrent_list = []

        for result in results:
            torrent_list.append({
                'hash': result.hashString,
                'eta': result.format_eta(),
                'status': result.status,
                'progress': float('%.3f' % result.progress),
                'name': result.name,
                'files': [val for key, val in result.files().iteritems()]
            })

        return torrent_list

    def pause_all(self):
        results = self.tc.get_torrents()

        for result in results:
            result.stop()

        return True

    def resume_all(self):
        results = self.tc.get_torrents()

        for result in results:
            result.start()

        return True

    def add_torrent(self, url):
        results = self.tc.add_torrent(url)
        return True

    def remove_torrent(self, torrent_hash):
        results = self.tc.remove_torrent(torrent_hash)
        return True

if __name__ == '__main__':
    tc = Torrents()
    results = tc.get_torrents()
    print json.dumps(results, indent=4)
