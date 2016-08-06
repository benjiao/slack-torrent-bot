import os
import time
import json
import re
from torrent_bot.torrents import Torrents
from slackclient import SlackClient


class TorrentBot:
    def __init__(self, slack_token, bot_name):
        self.slack_client = SlackClient(slack_token)
        self.websocket_delay = 1
        self.bot_name = bot_name
        self.bot_id = self.get_bot_id()

        self.tc = Torrents()

    def get_bot_id(self):
        api_call = self.slack_client.api_call("users.list")

        if api_call.get('ok'):
            users = api_call.get('members')

            for user in users:
                if user.get('name') == self.bot_name:
                    print "Bot ID: %s" % user.get('id')
                    return user.get('id')
        else:
            print "Cannot find Bot ID: %s" % self.bot_name

    def parse(self, message):
        if 'text' in message and message['text'].startswith("<@%s>: " % self.bot_id):
            message_text = message['text'].split("<@%s>: " % self.bot_id)[1]

            # Fetch All Torrents
            if re.match(r'.*status.*', message_text, re.IGNORECASE):
                torrent_list = self.tc.get_torrents()
                print torrent_list
                print json.dumps(torrent_list, indent=4)

                return {
                    'channel': message['channel'],
                    'message': "Here are your current downloads: ```%s```" % json.dumps(torrent_list, indent=4)
                }

            # Pause All Torrents
            elif re.match(r'.*pause all.*', message_text, re.IGNORECASE):
                response = self.tc.pause_all()
                print response

                return {
                    'channel': message['channel'],
                    'message': "I have paused all of your torrents!"
                }

            # Resume All Torrents
            elif re.match(r'.*resume all.*', message_text, re.IGNORECASE):
                response = self.tc.resume_all()
                print response

                return {
                    'channel': message['channel'],
                    'message': "I have resumed all of your torrents!"
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

                time.sleep(self.websocket_delay)

        else:
            print("Connection failed. Invalid Slack token or bot ID?")


if __name__ == '__main__':
    tbot = TorrentBot(slack_token=os.environ.get('TORRENTBOT_SLACK_TOKEN'), bot_name='torrentbot')
    tbot.run()
