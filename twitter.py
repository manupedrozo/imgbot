from datetime import timedelta
import requests
import base64

from util import *
from data_types import Metadata, Tweet, TweetMedia


class TwitterImgCrawler:
    def __init__(self, app_key: str, app_secret: str, metadata: Metadata, data_path: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = self._get_oauth2_token()
        self.base_url = 'https://api.twitter.com/2'
        self.headers = {"Authorization": "Bearer " + self.access_token}
        self.data_path = data_path
        self.metadata = metadata

    def _get_oauth2_token(self):
        # oauth2
        oauth2_url = "https://api.twitter.com/oauth2/token"
        bearer_token = base64.b64encode('{}:{}'.format(self.app_key, self.app_secret).encode('utf8'))
        headers = {
            'Authorization': 'Basic {0}'.format(bearer_token.decode('utf8')),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        res = requests.post(url=oauth2_url,
                            data={'grant_type': 'client_credentials'},
                            headers=headers)

        if res.status_code == 200:
            debug_log_response(res)
            access_token = res.json()["access_token"]
        else:
            debug_log_response(res, False)
            raise Exception("[CRAWLER] Twitter get token request failed")
        return access_token

    def _get(self, route: str, params: dict):
        url = self.base_url + route
        res = requests.get(url, params=params, headers=self.headers)
        if res.status_code == 200:
            debug_log_response(res)
        else:
            debug_log_response(res, False)
            raise Exception("[CRAWLER] Twitter request failed")  # TODO handle this
        return res.json()

    def _get_user_data_path(self, username) -> str:
        return os.path.join(os.path.abspath(self.data_path), f"{username}.json")

    def get_outdated_accounts(self) -> [str]:
        debug_log_info("[CRAWLER] Checking for outdated accounts...")
        result = []
        outdated_date = datetime.now() - timedelta(days=31)
        for username, info in self.metadata.accounts.items():
            if info.last_crawl is None or info.last_crawl < outdated_date:
                result.append(username)
        return result

    def crawl_account(self, username: str, max_tweets: int = 5, end_time: datetime = None) -> [Tweet]:
        if username not in self.metadata.accounts:
            raise Exception(f"[CRAWLER] Twitter username: @{username} not in known usernames")

        user_id = self.metadata.accounts[username].id
        debug_log_info(f"[CRAWLER] Crawling tweets from @{username} (id: {user_id})...")

        params = {
            'exclude': 'retweets',
            'expansions': 'attachments.media_keys',
            'tweet.fields': 'created_at',
            'media.fields': 'url'
        }
        if end_time is not None:
            params['end_time'] = date_to_string(end_time)

        tweets = []

        batch_size = 100  # Twitter API limit per request
        count = 0
        next_page_token = ''
        while count < max_tweets:
            remaining = max_tweets - count
            if remaining < batch_size:
                # Twitter API min allowed 'max_results' value is 5
                batch_size = remaining if remaining > 5 else 5

            # Set max results for next request
            params['max_results'] = batch_size
            # Set page for next request
            if count > 0:
                params['pagination_token'] = next_page_token

            res = self._get(route=f"/users/{user_id}/tweets", params=params)

            # We get a json with
            # - data: tweets basic info (and a media_key)
            # - includes.media: info for the media (with the media_key)
            # - meta: request & pagination info
            meta = res['meta']
            result_count = meta['result_count']
            next_page_token = meta['next_token']

            data = res['data']
            media = res['includes']['media']

            media_dict = {}  # {media_key: TweetMedia}
            for m in media:
                # Filter out non-image media
                if m['type'] == 'photo':
                    key = m['media_key']
                    media_dict[key] = TweetMedia(key=key, type=m['type'], url=m['url'])

            for i in range(result_count):
                tweet_data = data[i]
                tweet_media = []

                # Filter out non-media tweets
                if 'attachments' not in tweet_data:
                    continue

                # Associate tweet attachments to parsed img media
                for media_key in tweet_data['attachments']['media_keys']:
                    if media_key in media_dict:
                        tweet_media.append(media_dict[media_key])

                # Filter out non-media tweets
                if len(tweet_media) > 0:
                    tweet = Tweet(id=tweet_data['id'],
                                  created_at=date_from_string(tweet_data['created_at'], millis=True),
                                  text=tweet_data['text'],
                                  media=tweet_media)
                    tweets.append(tweet)

            count += result_count

            if result_count < batch_size:
                # We got less tweets than requested, stop here
                break

        debug_log_info(f"[CRAWLER] Crawled {count} tweets from @{username} (id: {user_id})")

        file_path = self._get_user_data_path(username)
        json_save([tweet.to_json() for tweet in tweets], file_path)

        debug_log_info(f"[CRAWLER] Crawled tweets saved to {file_path}")

        self.metadata.accounts[username].last_crawl = datetime.now()
        self.metadata.save()

        return tweets

    def get_account_tweet_files(self) -> [dict[str, str]]:
        """
        :return: [{username: username, file_path: path_to_account_tweets_file}]
        """
        result = []
        for username, info in self.metadata.accounts.items():
            file_path = self._get_user_data_path(username)
            if os.path.exists(file_path):
                result.append({'username': username, 'file_path': file_path})
        return result
