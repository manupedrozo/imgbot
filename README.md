# IMGBOT

**Twitter** image crawler & recommender

It will crawl twitter accounts for images, randomly pick 5, download them, and let you choose 1 to post.

Posting has to be manual, don't wanna get banned now, do we?

---

### Dir structure:
- config
    - example.json -> Example config
    - config.json -> Provided by user, twitter api dev credentials
- data
    - metadata.json -> account metadata, user fills this with accounts to crawl
    - history.json -> previously selected images
    - [account username].json -> crawled tweets for the account
- img -> images will be downloaded here (and deleted after selection)
    - [img-index].jpg

The dir structure is initialized when running for the first time. Including a sample metadata file.

---

### Working method:
- User provides a ./config/config.json file with a twitter [app_key] and [app_secret]
    - You will need to sign up for a twitter dev account, just google it m8 :)
- Crawl \<1000> latest tweets from each account
    - Save tweets to disk (./data/[username].json)
    - Tweets are crawled once per month per account, overwriting the previous crawl for that account
- Use saved tweets to give image choices
    - \<5> tweets are randomly chosen, and their images are downloaded to ./img/[img-index].jpg
    - File explorer is opened at ./img
    - User chooses 1 image (through terminal)
    - Chosen images are saved to History (./data/history.json) to avoid repetition in the future
    - The rest are deleted
- User may chose to open \<instagram> to post the image

---

*Made in 1 day, it's not bulletproof*
