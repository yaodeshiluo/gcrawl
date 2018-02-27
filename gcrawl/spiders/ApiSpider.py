#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from random import uniform
from datetime import datetime
import gevent
from gSpider.spiders import Spider
from gSpider import Request
from gcrawl.pipelines import pipeline


class ApiSpider(Spider):

    name = 'api'

    def __init__(self, *args, **kwargs):
        super(ApiSpider, self).__init__(*args, **kwargs)
        self.lottery_info = kwargs.pop('lottery_info')
        _ = kwargs.pop('start_urls', [])
        if _:
            self.start_urls = _
        self.request_kwargs = kwargs.pop('request_kwargs', {})
        self.interval = 10
        self.next_time = None

    @property
    def period(self):
        if not hasattr(self, '_period'):
            period = self.lottery_info.get('period')
            if not period:
                self._period = None
            else:
                period_start, period_end = map(lambda s: tuple(map(int, s.split(':'))), period.split('-'))
                # period_start提前1分钟, period_end延后2分钟
                seconds_start = (period_start[0] * 3600 + period_start[1] * 60) - 60
                if seconds_start <= 0:
                    period_start = (0, 0)
                else:
                    period_start = (seconds_start / 3600, (seconds_start % 3600) / 60)

                seconds_end = (period_end[0] * 3600 + period_end[1] * 60) + 120
                if seconds_end >= 23 * 3600 + 59 * 60:
                    period_end = (23, 59)
                else:
                    period_end = (seconds_end / 3600, (seconds_end % 3600) / 60)
                self._period = (period_start, period_end)
        return self._period

    def _sleep(self):
        gevent.sleep(int(uniform(0.8, 1.2) * self.interval))

    # 什么时候开始抓取
    def _how_lone_before_start(self):
        period = self.period
        if not period:
            return 0
        now = datetime.now()
        now_h, now_minute = now.hour, now.minute

        period_start, period_end = period
        if period_start[0] <= period_end[0]:
            if (now_h, now_minute) < period_start:
                return (period_start[0] * 3600 + period_start[1] * 60) - (now_h * 3600 + now_minute * 60)
            if (now_h, now_minute) > period_end:
                return (24 * 3600) - (now_h * 3600 + now_minute * 60) + (period_start[0] * 3600 + period_start[1] * 60)
        else:
            if period_end < (now_h, now_minute) < period_start:
                return (period_start[0] * 3600 + period_start[1] * 60) - (now_h * 3600 + now_minute * 60)
        return 0

    def wait_to_start(self):
        wait_seconds = self._how_lone_before_start()
        if wait_seconds > 0:
            gevent.sleep(wait_seconds)

    def sleep(self):
        if self.next_time is not None:
            now = datetime.now()
            if now >= self.next_time:
                self._sleep()
            else:
                gevent.sleep((self.next_time - now).total_seconds())
        else:
            self._sleep()

    def start_requests(self):
        while True:
            self.wait_to_start()
            for url in self.start_urls:
                yield Request(url, callback=self.parse, **self.request_kwargs)
                self.sleep()

    def parse(self, response):
        data = json.loads(response.body)
        for each in data:
            item = {}
            item['key'] = self.lottery_info['key']
            item['name'] = self.lottery_info.get('name', '')
            item['src'] = self.lottery_info['src']

            item['issue'] = each.get('issue_no', '')
            item['open_time'] = each.get('prize_time', '')
            item['result'] = each.get('prize_number', '')
            item = pipeline(item, self)
            yield item
