#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gSpider.crawler import CrawlerRunner
from spiders_conf import get_all


runner = CrawlerRunner({})

for spidercls, kwargs_list in get_all().iteritems():
    for kwargs in kwargs_list:
        runner.crawl(spidercls, **kwargs)

runner.join()
