# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import datetime, date
from bs4 import BeautifulSoup

class DetikNewsSpider(scrapy.Spider):
    name = 'detik_news'
    allowed_domains = ['news.detik.com']

    def start_requests(self):
        base_url = 'https://news.detik.com/indeks/?date={}/{}/{}'

        # we will start crawling from today's news
        today = datetime.today()
        while (True):
            # first get the year (YYYY), month (MM), and day (DD) of the today's date
            year = str(today.year)
            month = ('0' if len(str(today.month)) == 1 else '') + str(today.month)
            day = ('0' if len(str(today.day)) == 1 else '') + str(today.day)

            # concat it to be the URL to crawl
            crawl_url = base_url.format(month, day, year)

            # start crawling
            yield scrapy.Request(crawl_url, self.parse)

            # now we can go to the day before and start crawling again
            today = date.fromordinal(today.toordinal() - 1)

    def parse(self, response):
        # get every news link in the index page
        news_urls = response.css('h3.media__title > a::attr(href)').extract()
        for news_url in news_urls:
            yield scrapy.Request(url=response.urljoin(news_url), callback=self.parse_news)

        # follow pagination links
        pagination = response.css('div.pagination > a::attr(href)')
        if len(pagination) > 0:
            next_page_url = pagination[-1].extract()
            if next_page_url:
                yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_news(self, response):
        # parse the news body text
        body_text = response.css('div.detail__body-text').extract_first()
        if body_text:
            # if this is from second/next page of other news, then we have to
            # concat the news from previous page
            if response.meta != None and 'result' in response.meta:
                result = response.meta['result']
            else:
                result = {
                    'title': response.css('h1.detail__title::text').extract_first().strip(),
                    'author': response.css('div.detail__author::text').extract_first().strip(),
                    'date': response.css('div.detail__date::text').extract_first().strip(),
                    'url': response.url,
                    'news': ''
                }

            # clean the body text and detect it there is/are next page(s) in this news
            news = self.clean_html(body_text)
            
            # append the news first
            result['news'] = result['news'] + (' ' if len(result['news']) > 0 else '') + news.strip()
            
            # follow next page
            next_page_url = response.css('div.detail__body-text > div.detail__long-nav > a::attr(href)').extract_first()
            if next_page_url != None:
                yield scrapy.Request(url=next_page_url,
                                    callback=self.parse_news,
                                    meta={'result': result})
            else:
                yield result

    def clean_html(self, result):
        # parse the html result with bs4 library
        soup = BeautifulSoup(result, 'html.parser')

        # these are list of tag we want to delete
        decompose_list = [
            soup(['script', 'style']),
            soup.find_all('div', {'class': 'lihatjg'}),
            soup.find_all('a', {'class', 'embed video20detik'}),
            soup.find_all('div', {'class', 'detail__body-tag mgt-16'}),
            soup.find_all('div', {'class', 'ratiobox ratio_16_9 sisip_video_ds'}),
        ]
        # flatten the list of list
        flatten_decompose_list = [item for sublist in decompose_list for item in sublist]
        # delete the tags
        for script in flatten_decompose_list:
            script.decompose()

        # concat the news
        news = ' '.join(soup.stripped_strings).strip()

        # delete the city name in front of every news text
        index = news.find("-")
        if index != -1:
            news = news[index+1:]

        # delete some leftover texts
        delete_start_from_index = lambda index: news[:index-1] if index != -1 else news
        texts_to_delete = [
            'Selanjutnya Halaman 1',
            'Halaman 1'
        ]
        for text_to_delete in texts_to_delete:
            news = delete_start_from_index(news.rfind(text_to_delete))

        # delete the contributors sign using regex, e.g. (aaa/bbb)
        p = re.compile(r'\([\w\d]+\/[\w\d]+\)$')
        news = p.sub('', news)

        return news
