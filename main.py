from random import randrange
import subprocess
import webbrowser
import requests

from twitter import TwitterImgCrawler
from data_types import *
from util import *

abspath = os.path.abspath

RECOMMENDATION_COUNT = 5
TWEETS_PER_ACCOUNT = 1000

CONFIG_PATH = abspath("./config/config.json")
DATA_DIR = abspath("./data")
METADATA_PATH = abspath("./data/metadata.json")
HISTORY_PATH = abspath("./data/history.json")
IMAGE_DIR = abspath("./img")
WEBSITE = "https://www.instagram.com/create/select/"


def init_dir_structure():
    debug_log_info(f"Initializing dir structure...")
    if not os.path.exists(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)
        debug_log_info(f"Created {IMAGE_DIR}")
    else:
        debug_log_info(f"{IMAGE_DIR} already present")

    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
        debug_log_info(f"Created {DATA_DIR}")
    else:
        debug_log_info(f"{DATA_DIR} already present")

    if not os.path.exists(HISTORY_PATH):
        history = History(file_path=HISTORY_PATH, tweets=[], last_update=datetime.now())
        history.write()
        debug_log_info(f"Created {HISTORY_PATH}")
    else:
        debug_log_info(f"{HISTORY_PATH} already present")

    if not os.path.exists(METADATA_PATH):
        sample_metadata = Metadata(
            file_path=METADATA_PATH,
            accounts={
                "username1": AccountMetadata("123456", "username1", None),
                "username2": AccountMetadata("654321", "username2", None)
            },
            last_update=datetime.now()
        )
        sample_metadata.save()
        print(f"Sample metadata file created at {METADATA_PATH}, fill it and come back!")
        exit("Exiting...")
    else:
        debug_log_info(f"{METADATA_PATH} already present")


def download_image(url: str, target_path: str):
    debug_log_info(f"Downloading img from {url} into {target_path}...")
    with open(target_path, 'wb') as f:
        res = requests.get(url, stream=True)

        if res.status_code == 200:
            for data in res.iter_content(1024):
                if not data:
                    break
                f.write(data)
            debug_log_info(f"{target_path} downloaded successfully")
        else:
            debug_log_response(res, False)


def main():
    # --- INIT ---
    init_dir_structure()

    # load config
    config = json_load(CONFIG_PATH)
    if not config['twitter']['app_key'] or not config['twitter']['app_secret']:
        exit("Twitter app_key or app_secret not present, exiting...")

    # load metadata
    metadata = Metadata.load(METADATA_PATH)
    if len(metadata.accounts) == 0:
        print("Your metadata file has no accounts, there is nothing to crawl!")
        exit("Exiting...")

    # --- CRAWLER ---
    crawler = TwitterImgCrawler(
        config['twitter']['app_key'],
        config['twitter']['app_secret'],
        metadata,
        DATA_DIR
    )

    outdated_accounts = crawler.get_outdated_accounts()

    for username in outdated_accounts:
        crawler.crawl_account(username=username, max_tweets=TWEETS_PER_ACCOUNT)

    # --- RECOMMENDER ---

    # load history
    history = History.study(HISTORY_PATH)

    # This is really dumb :)
    # Throwing together all the "recommender" & user interaction code here, needs a refactor
    debug_log_info(f"Stupidly selecting {RECOMMENDATION_COUNT} random images...")

    # Get some random tweets from tweet files
    recommendations: [Tweet] = []
    crawled_accounts = crawler.get_account_tweet_files()
    account_count = len(crawled_accounts)
    rec_i = 0
    while rec_i < RECOMMENDATION_COUNT:
        rand_acc = randrange(0, account_count)
        account = crawled_accounts[rand_acc]
        with open(account['file_path'], 'r') as f:
            tweets_json = json.load(f)
            rand_tweet = randrange(0, len(tweets_json))
            tweet = Tweet.from_json(tweets_json[rand_tweet])

            already_in_history = history.contains(tweet)
            if already_in_history:
                debug_log_info(f"Tweet {tweet.id} already in history, rerolling...")
            else:
                recommendations.append(tweet)
                debug_log_data(tweet)
                rec_i += 1

    # Download images for the randomly selected tweets
    downloads = {}  # {file_name: file_path}
    rec_dict = {}  # {file_name: Tweet} (to write chosen to history)
    img_dir = os.path.abspath(IMAGE_DIR)
    for i, rec in enumerate(recommendations):
        suffix = ''
        for j, img in enumerate(rec.media):
            if j > 0:
                suffix = f'-{j}'
            img_name = f"{i}{suffix}"
            img_path = os.path.join(img_dir, f'{img_name}.jpg')
            download_image(img.url, img_path)
            downloads[img_name] = img_path
            rec_dict[img_name] = rec

    # Open file explorer to choose image and handle user input
    subprocess.Popen(f'explorer "{img_dir}"')  # TODO support other OSs (this is windows only)
    while True:
        print("Insert image to post (no ext):")
        user_input = input()
        if user_input == '-1':
            break
        elif user_input in downloads:
            selected = downloads[user_input]
            downloads.pop(user_input)

            print(f"{selected} it is!")
            history.tweets.append(rec_dict[user_input])
            history.write()
            break
        else:
            print("That's the wrong number, try again (-1 to exit)...")

    # Delete all images that weren't chosen
    print("Cleaning up...")
    for to_delete in downloads.values():
        os.remove(to_delete)

    # Open website where to post the image
    if WEBSITE:
        print(f"Open {WEBSITE}? (y/n):")
        user_input = input()
        if user_input == "y":
            print("Opening web browser...")
            webbrowser.open(WEBSITE)


if __name__ == '__main__':
    print("Ready?")
    input()
    main()
