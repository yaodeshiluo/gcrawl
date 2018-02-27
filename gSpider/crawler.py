#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gevent
from gevent import monkey
monkey.patch_all()
from gSpider.core.engine import ExecutionEngine


class Crawler(object):

    def __init__(self, spidercls, settings=None):
        self.spidercls = spidercls
        self.settings = settings.copy()
        self.crawling = False
        self.spider = None
        self.engine = None

    def crawl(self, *args, **kwargs):
        assert not self.crawling, "Crawling already taking place"
        self.crawling = True
        try:
            self.spider = self._create_spider(*args, **kwargs)
            print type(self.spider), self.spider
            self.engine = self._create_engine()
            start_requests = self.spider.start_requests()
            self.engine.open_spider(self.spider, start_requests)
        except Exception:
            raise

    def _create_spider(self, *args, **kwargs):
        return self.spidercls.from_crawler(self, *args, **kwargs)

    def _create_engine(self):
        return ExecutionEngine(self, lambda _: self.stop())

    def stop(self):
        if self.crawling:
            self.crawling = False
            self.engine.stop()


class CrawlerRunner(object):

    crawlers = property(
        lambda self: self._crawlers,
        doc="Set of :class:`crawlers <scrapy.crawler.Crawler>` started by "
            ":meth:`crawl` and managed by this class."
    )

    def __init__(self, settings=None):
        self.settings = settings
        self._crawlers = set()
        self._active = False

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        crawler = self.create_crawler(crawler_or_spidercls)
        return self._crawl(crawler, *args, **kwargs)

    def _crawl(self, crawler, *args, **kwargs):
        d = gevent.spawn(lambda: crawler.crawl(*args, **kwargs))
        self.crawlers.add(d)
        return d

    def create_crawler(self, crawler_or_spidercls):
        if isinstance(crawler_or_spidercls, Crawler):
            return crawler_or_spidercls
        return Crawler(crawler_or_spidercls, self.settings)

    def join(self):
        self._active = True
        gevent.joinall(self.crawlers)
        self._active = False
