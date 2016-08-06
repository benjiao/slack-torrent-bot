import os
import re
import time
import json
from torrent_bot.torrents import TorrentController
from torrent_bot.responses import ResponseGenerator
from slackclient import SlackClient


class TorrentBot:
    def __init__(self, config_file='~/torrent-bot.json'):
        self.config = self.load_config(config_file)

        self.slack_client = SlackClient(self.config['slack']['token'])
        self.slack_bot_name = self.config['slack']['bot-name']
        self.slack_bot_id = self.get_bot_id()

        self.torrent_controller = TorrentController(config=self.config)
        self.response_generator = ResponseGenerator()

    def load_config(self, config_file):
        config_file_path = os.path.expanduser(config_file)
        print "Config: %s" % config_file_path

        with open(config_file_path, 'r') as fp:
            return json.load(fp)

    def get_bot_id(self):
        api_call = self.slack_client.api_call("users.list")

        if api_call.get('ok'):
            users = api_call.get('members')

            for user in users:
                if user.get('name') == self.slack_bot_name:
                    print "Bot ID: %s" % user.get('id')
                    return user.get('id')
        else:
            print "Cannot find Bot ID: %s" % self.slack_bot_name

    def parse(self, message):
        if 'text' in message and message['text'].startswith("<@%s>: " % self.slack_bot_id):
            message_text = message['text'].split("<@%s>: " % self.slack_bot_id)[1]

            # Fetch All Torrents
            if re.match(r'.*(status|list (of )*all).*', message_text, re.IGNORECASE):
                torrent_list = self.torrent_controller.get_torrents()
                print json.dumps(torrent_list, indent=4)

                if len(torrent_list) == 0:
                    return {
                        'channel': message['channel'],
                        'message': "There are no torrents in your list"
                    }

                return {
                    'channel': message['channel'],
                    'message': self.response_generator.response('fetch-all', {'torrents': torrent_list})
                }

            # Pause All Torrents
            elif re.match(r'.*(stop|pause) all.*', message_text, re.IGNORECASE):
                self.torrent_controller.pause_all()

                return {
                    'channel': message['channel'],
                    'message': "I have paused all of your torrents!"
                }

            # Resume All Torrents
            elif re.match(r'.*(start|resume|continue) all.*', message_text, re.IGNORECASE):
                self.torrent_controller.resume_all()

                return {
                    'channel': message['channel'],
                    'message': "I have resumed all of your torrents!"
                }

            # Add torrent
            elif re.match(r'.*(add|download).*(http://.*.torrent).*', message_text, re.IGNORECASE):
                search_results = re.search(r'http://(.*).torrent', message_text).group(0)
                self.torrent_controller.add_torrent(search_results)

                return {
                    'channel': message['channel'],
                    'message': "Okay!"
                }

            # Remove torrent
            elif re.match(r'.*(remove|cancel|delete).*[0-9a-z]{40}', message_text, re.IGNORECASE):
                search_results = re.search(r'[0-9a-z]{40}', message_text).group(0)
                self.torrent_controller.remove_torrent(search_results)

                return {
                    'channel': message['channel'],
                    'message': "Done!"
                }

            # Default message
            else:
                return {
                    'channel': message['channel'],
                    'message': "Huh?"
                }

        return None

    def run(self):
        if self.slack_client.rtm_connect():
            print("Starting TorrentBot...")

            while True:
                parser_results = [x for x in map(self.parse, self.slack_client.rtm_read()) if x is not None]

                if len(parser_results) > 0:
                    print 'Parser results: %s' % json.dumps(parser_results, indent=4)
                    for response in parser_results:
                        self.slack_client.api_call(
                            "chat.postMessage",
                            channel=response['channel'],
                            text=response['message'],
                            as_user=True)

                time.sleep(self.config['websocket-delay'])

        else:
            print("Connection failed. Invalid Slack token or bot ID?")


if __name__ == '__main__':
    config_file = os.environ.get('TORRENTBOT_CONFIG', '~/torrent-bot.json')
    tbot = TorrentBot(config_file=config_file)
    tbot.run()
