import sys
import os
import re
import json
import time
from datetime import datetime
import requests
import logging
import cleanup
from api_keys import BT


# logの設定
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
fmt = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%dT%H:%M:%S")

# コンソール用ハンドラ
handler1 = logging.StreamHandler(sys.stdout)
handler1.setFormatter(fmt)

# ログファイル用ハンドラ
handler2 = logging.FileHandler(filename="logger.log")
handler2.setLevel(logging.WARNING)
handler2.setFormatter(fmt)

logger.addHandler(handler1)
logger.addHandler(handler2)

# MAXの文字数
TWEET_LEN = 140

# 日本語かどうかをチェック
is_ja = re.compile(r'.*[ぁ-んァ-ン].*')


class RepliesCollecter:

    def __init__(self):

        self.lang = "ja"

        if not os.path.exists("corpus"):
            os.makedirs("corpus")
        self.dumpfile = "corpus/%s_%s.txt" % (self.lang,
                                              datetime.now().strftime("%Y%m%d_%H%M%S"))

    def streaming(self):
        """
        ストリーミングでツイートを収集する。

        """
        params = {"expansions": 'author_id,referenced_tweets.id'}

        url = "https://api.twitter.com/2/tweets/sample/stream"
        wait_cnt = 0
        retry_cnt = 0

        res = requests.get(
            url, headers={'Authorization': 'Bearer '+BT}, params=params, stream=True)

        if res.status_code == 200:

            wait_cnt = 0
            retry_cnt = 0
            for res_line in res.iter_lines():

                if not res_line:
                    continue
                result = json.loads(res_line.decode('utf-8'))

                if 'errors' in result:
                    continue

                if len(result['includes']['tweets']) < 1:
                    continue

                if 'referenced_tweets' not in result['includes']['tweets'][0]:
                    continue

                if result['includes']['tweets'][0]['referenced_tweets'][0]['type'] != 'replied_to':
                    continue

                a_tweet = result['includes']['tweets'][1]
                b_tweet = result['includes']['tweets'][0]

                if a_tweet['author_id'] == b_tweet['author_id']:
                    continue

                tweets = [self.formatTweet(
                    a_tweet["text"]), self.formatTweet(b_tweet["text"])]

                if (not bool(is_ja.match(tweets[0]))) or (not bool(is_ja.match(tweets[1]))):
                    continue

                if (1 < len(tweets[0]) < TWEET_LEN) and (1 < len(tweets[1]) < TWEET_LEN):
                    self.dump(tweets)
                    logger.debug(result)
                    logger.info("A: {}".format(tweets[0]))
                    logger.info("B: {}".format(tweets[1]))
                    print("--------------------------------------------")

        elif res.status_code == 420 or res.status_code == 429:
            logger.warning("HTTP {} Code. {}".format(
                res.status_code, res.text))
            wait_cnt += 1
            time.sleep(900 * wait_cnt)

        else:
            logger.warning("Cannot get stream... (HTTP{}): {}".format(
                res.status_code, res.text))
            retry_cnt += 1
            time.sleep(300)
            if retry_cnt > 5:
                logger.error(
                    "The program was stopped due to error continued for more than 5 times.")
                sys.exit()

    def formatTweet(self, line):
        """
        得られたツイートをフォーマットする
        """
        return cleanup.sentence(line)

    def dump(self, tweets):
        """
        コーパスファイルの保存
        """
        with open(self.dumpfile, "a") as fdump:
            fdump.write("%s\n%s\n" % (tweets[0], tweets[1]))


def main():
    while True:
        try:
            collecter = RepliesCollecter()
            try:
                logger.info("Start.")
                collecter.streaming()
            except KeyboardInterrupt:
                logger.warning("Keyboard Interrupt!")
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                logger.warning(e)
                time.sleep(600)
                continue
            except Exception as e:
                logger.error(e)
                time.sleep(300)
                continue
        finally:
            logger.info("Exit successful! corpus dumped in %s" %
                        (collecter.dumpfile))


if __name__ == '__main__':
    sys.exit(main())
