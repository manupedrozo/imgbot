from dataclasses import dataclass

from util import *


@dataclass
class AccountMetadata:
    id: str
    username: str
    last_crawl: datetime  # Nullable

    def to_json(self):
        result = self.__dict__.copy()
        result['last_crawl'] = date_to_string(self.last_crawl) if self.last_crawl else ''
        return result

    @staticmethod
    def from_json(obj_json: dict):
        result = AccountMetadata(
            id=obj_json['id'],
            username=obj_json['username'],
            last_crawl=date_from_string(obj_json['last_crawl']) if obj_json['last_crawl'] else None
        )
        return result


@dataclass
class Metadata:
    file_path: str
    accounts: dict[str, AccountMetadata]
    last_update: datetime

    @staticmethod
    def load(file_path: str):
        debug_log_info(f"[META] Loading metadata from {file_path}...")

        obj_json = json_load(file_path)
        accounts = {}
        for key, value in obj_json['accounts'].items():
            accounts[key] = AccountMetadata.from_json(value)

        result = Metadata(
            file_path=file_path,
            accounts=accounts,
            last_update=date_from_string(obj_json['last_update'])
        )

        debug_log_info("[META] Metadata loaded")
        return result

    def save(self):
        debug_log_info(f"[META] Saving metadata to {self.file_path}...")
        self.last_update = datetime.now()
        obj = {
            'accounts': dict((k, v.to_json()) for k, v in self.accounts.items()),
            'last_update': date_to_string(self.last_update)
        }
        json_save(obj, self.file_path)
        debug_log_info("[META] Metadata saved")


@dataclass
class TweetMedia:
    key: str
    type: str
    url: str

    def to_json(self):
        return self.__dict__

    @staticmethod
    def from_json(json: dict):
        result = TweetMedia(**json)
        return result


@dataclass
class Tweet:
    id: str
    created_at: datetime
    text: str
    media: [TweetMedia]

    def to_json(self):
        result = self.__dict__.copy()
        result['created_at'] = date_to_string(self.created_at)
        result['media'] = [media.to_json() for media in self.media]
        return result

    @staticmethod
    def from_json(obj_json: dict):
        result = Tweet(
            id=obj_json['id'],
            created_at=date_from_string(obj_json['created_at']),
            text=obj_json['text'],
            media=[TweetMedia.from_json(media) for media in obj_json['media']]
        )
        return result


@dataclass
class History:
    file_path: str
    tweets: [Tweet]
    last_update: datetime

    # But muh naming convention BabyRage
    @staticmethod
    def study(file_path):
        debug_log_info(f"[HISTORY] Studying history from {file_path}...")
        obj_json = json_load(file_path)
        result = History(
            file_path=file_path,
            tweets=[Tweet.from_json(j) for j in obj_json['tweets']],
            last_update=date_from_string(obj_json['last_update'])
        )
        debug_log_info(f"[HISTORY] History studied")
        return result

    def write(self):
        debug_log_info(f"[HISTORY] Writing history to {self.file_path}...")
        self.last_update = datetime.now()
        obj = {
            'tweets': [tweet.to_json() for tweet in self.tweets],
            'last_update': date_to_string(self.last_update)
        }
        json_save(obj, self.file_path)
        debug_log_info("[HISTORY] History has been written")

    def contains(self, tweet: Tweet):
        for t in self.tweets:
            if t.id == tweet.id:
                return True
        return False
