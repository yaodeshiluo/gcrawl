#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
import json
from gevent.local import local
import requests
from pymongo import MongoClient
from gSpider.exceptions import DropItem
from gcrawl.utils.issue import get_ymd_b


class SavePipeline(object):

    def __init__(self):
        self.store = local()
        self.server_url = 'http://base.icaipiao123.com/input/v1/input/batch'
        self.timeout = 5
        self.schedule = dict()
        self.mongo_client = MongoClient()

    def process_item(self, item, spider):
        last_item = getattr(self.store, 'last_item', None)
        self.save(item)
        if last_item is None or last_item['issue'] < item['issue']:
            self.store.last_item = item
            print 'last_item', item['issue'], item['key']
            self.set_spider_next_start_time(spider, item)
        return item

    def to_server(self, item):
        try:
            print 'send to server, item issue:', item['issue']
            data = json.dumps({'data': [item]})
            r = requests.post(self.server_url, data=data, timeout=self.timeout)
            item['status'] = r.text
            print r.text
        except Exception:
            pass

    def save(self, item):
        collection = self.mongo_client.caipiao.test
        cond = {'key': item['key'], 'src': item['src'], 'issue': item['issue']}
        _item = collection.find_one(cond)
        if not _item:
            self.to_server(item)
            item['create_time'] = datetime.now()
            collection.insert(item)

    def set_spider_next_start_time(self, spider, last_item):
        last_issue = last_item['issue']
        y, m, d, b = get_ymd_b(last_issue)
        issue_day = datetime(y, m, d)
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        if (today - issue_day).days <= 1:
            key = last_item['key']
            schedule = self.get_schedule(key)

            next_hm = schedule.get(b + 1)
            if not next_hm:
                return
            if (today - issue_day).days == 1 and '+' not in next_hm:
                return
            next_time = datetime(now.year, now.month, now.day, *(map(int, next_hm.split(':')))) - timedelta(minutes=1)
            spider.next_time = next_time

            # 更新self.schedule
            cur_hm = schedule.get(b)
            self.set_schedule(key, (b, cur_hm))

    def get_schedule(self, key):
        if key in self.schedule:
            return self.schedule.get(key)
        return self.schedule.setdefault(key, self.get_schedule_from_mongo(key))

    def set_schedule(self, key, b_and_cur_hm):
        now = datetime.now()
        now_hm = '%02d:%02d' % (now.hour, now.minute)
        b, cur_hm = b_and_cur_hm

        ret = self._cmp_and_fmt(now_hm, cur_hm)
        if ret:
            self.schedule.setdefault(key, {})[b] = ret

    @staticmethod
    def _cmp_and_fmt(new, old):
        new_h, new_m = map(int, new.split(':'))
        old_h, old_m = map(int, old.split(':'))
        r1 = range(22, 24)
        r2 = range(0, 2)
        if new_h in r1 and old_h in r2:
            return new
        elif new_h in r2 and old_h in r1:
            return None
        else:
            if (new_h, new_m) < (old_h, old_m):
                if '+' in old:
                    new = '+' + new
                return new
            return None

    def get_schedule_from_mongo(self, key):
        schedule_collection = self.mongo_client.config.schedule
        ret = schedule_collection.find_one({'key': key})
        return eval(ret['hm']) if ret else {}

    def close_spider(self):
        self.mongo_client.close()


class FormatPipeline(object):

    def process_item(self, item, spider):
        to_update = {}
        for field in ['key', 'issue', 'result', 'open_time']:
            if field not in item:
                raise DropItem('%s not in item' % field)
        for field, field_value in item.iteritems():
            new_field_value = self.format(field, field_value)
            if new_field_value != field_value:
                to_update[field] = new_field_value
        if to_update:
            item.update(to_update)
        return item

    def format(self, field, field_value):
        if field == 'open_time':
            return self.format_open_time(field_value)
        elif field == 'result':
            return self.format_result(field_value)
        elif field == 'issue':
            return self.format_issue(field_value)
        return field_value

    @staticmethod
    def format_open_time(open_time):
        try:
            args = map(int, re.split(r'[^\d]+', open_time))
            if args[0] < 100:
                args[0] += 2000
            fmt = '%Y-%m-%d %H:%M:%S' if len(args) >= 5 else '%Y-%m-%d'
            return datetime(*args).strftime(fmt)
        except Exception:
            raise DropItem('invalid open_time: %s' % open_time)

    @staticmethod
    def format_result(result):
        try:
            ret = ','.join(re.split(r'[^\d]+', result))
            if not ret:
                raise
            return ret
        except Exception:
            raise DropItem('invalid result: %s' % result)

    @staticmethod
    def format_issue(issue):
        try:
            ret = filter(lambda _: _.isdigit(), issue)
            if not ret:
                raise
            return ret
        except Exception:
            raise DropItem('invalid issue: %s' % issue)


p1 = FormatPipeline()
p2 = SavePipeline()


def pipeline(item, spider):
    try:
        item = p1.process_item(item, spider)
        item = p2.process_item(item, spider)
        return item
    except DropItem, e:
        print 'DropItem', e
