# DetikNews Crawler

This is a crawler for extracting news from the DetikNews [https://news.detik.com](https://news.detik.com). The extracted data are the news title, author names, publication datetime, news content, and the URL.

The spider will crawl the index page from today's date until the spider is terminated or it has crawled all news in the website.

## Installation
1. Clone this repository
2. The code is written in Python 3.8.5. Install the dependencies by running `pip install -r requirements.txt`
3. Change your directory
3. Run `scrapy crawl detik_news -o news.json` to run the spider and save all scraped items in `news.json` file.
