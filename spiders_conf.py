#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import deepcopy
from gcrawl.spiders.ApiSpider import ApiSpider


lottery_period = {
    'shandong_11yunduojin': '8:37-22:57',
    'shanghai_n11x5': '9:01-23:51',
    'jiangxi_n11x5': '9:10-23:00',
    'guangdong_n11x5': '9:10-23:00',
    'anhui_n11x5': '8:42-22:02',
    'anhui_lekuai3': '8:50-22:00',
    'jilin_xinkuai3': '8:29-22:49',
    'guangxi_kuai3': '9:38-22:28',
    'hubei_kuai3': '9:10-22:00',
    'xinjiang_shishicai': '10:10-+2:00',
    'tianjin_shishicai': '9:12-23:02',
    'chongqing_shishicai': '10:00-+2:00',
}


spiders_conf = {
    ApiSpider: {
        'common': {
            'start_urls': ['https://www.cpcp31.com/index'],
            'lottery_info': {
                'key': 'shandong_11yunduojin',
                'name': u'山东11选5',
                'src': 'https://www.cpcp31.com-api'
            },
            'request_kwargs': {
                'headers': {'accept': 'application/json',
                            'Connection': 'close',
                            'accept-encoding': 'gzip, deflate, br',
                            'accept-language': 'zh-CN,zh;q=0.8,en;q=0.6',
                            'authorization': '60539db10398aa49444d898e2d05148b',
                            'origin': 'https://www.cpcp31.com',
                            'referer': 'https://www.cpcp31.com/',
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'},
                'method': 'POST',
                'body': {"act": 512, "lottery_id": 11, "count": 50},
            }
        },
        'each': [
            {},
            {
                'lottery_info': {'key': 'shanghai_n11x5', 'name': u'上海11选5'},
                'request_kwargs': {
                    'headers': {'authorization': '3f083f45a1b47ff52ca93f6ab08ac7b4'},
                    'body': {'lottery_id': 12}
                }
            },
            {
                'lottery_info': {'key': 'jiangxi_n11x5', 'name': u'江西11选5'},
                'request_kwargs': {
                    'headers': {'authorization': '363b0ca5ff0aea9aa8ae0d9f579fd4a3'},
                    'body': {'lottery_id': 13}
                }
            },
            {
                'lottery_info': {'key': 'guangdong_n11x5', 'name': u'广东11选5'},
                'request_kwargs': {
                    'headers': {'authorization': 'b9c295c6cb0be6e8ef4d6dea21863d81'},
                    'body': {'lottery_id': 14}
                }
            },
            {
                'lottery_info': {'key': 'anhui_n11x5', 'name': u'安徽11选5'},
                'request_kwargs': {
                    'headers': {'authorization': '585d04e14296daa9eed73fc037337933'},
                    'body': {'lottery_id': 15}
                }
            },
            {
                'lottery_info': {'key': 'anhui_lekuai3', 'name': u'安徽快3'},
                'request_kwargs': {
                    'headers': {'authorization': 'b5a5317b9ec3a0ac49bc4cf67c6bd0f9'},
                    'body': {'lottery_id': 6}
                }
            },
            {
                'lottery_info': {'key': 'jilin_xinkuai3', 'name': u'吉林快3'},
                'request_kwargs': {
                    'headers': {'authorization': '3f4c502215237433e7b3aa744ba58621'},
                    'body': {'lottery_id': 7}
                }
            },
            {
                'lottery_info': {'key': 'guangxi_kuai3', 'name': u'广西快3'},
                'request_kwargs': {
                    'headers': {'authorization': '4fbd7ef0b2ecfeece61befff74777aab'},
                    'body': {'lottery_id': 8}
                }
            },
            {
                'lottery_info': {'key': 'hubei_kuai3', 'name': u'湖北快3'},
                'request_kwargs': {
                    'headers': {'authorization': 'b99b583aaf1aeb4d730ae13fb4014848'},
                    'body': {'lottery_id': 10}
                }
            },
            {
                'lottery_info': {'key': 'xinjiang_shishicai', 'name': u'新疆时时彩'},
                'request_kwargs': {
                    'headers': {'authorization': 'c6008f1cf941715ed3c1dc5b5186d1a8'},
                    'body': {'lottery_id': 2}
                }
            },
            {
                'lottery_info': {'key': 'tianjin_shishicai', 'name': u'天津时时彩'},
                'request_kwargs': {
                    'headers': {'authorization': '4efbc59719341053025567d92e9488fd'},
                    'body': {'lottery_id': 4}
                }
            },
            {
                'lottery_info': {'key': 'chongqing_shishicai', 'name': u'重庆时时彩'},
                'request_kwargs': {
                    'headers': {'authorization': 'd76bfc80b73cbc2e7ebe0e3e75a4e83d'},
                    'body': {'lottery_id': 1}
                }
            },
        ]
    }
}


def merge_dict(common, each):
    common = deepcopy(common)
    for each_k, each_v in each.items():
        common_v = common.get(each_k)
        if common_v is None:
            common[each_k] = each_v
        elif isinstance(each_v, dict):
            if isinstance(common_v, dict):
                common[each_k] = merge_dict(common_v, each_v)
        elif each_v != common_v:
            common[each_k] = each_v
    return common


def get_all():
    ret = {}
    for spidercls, conf in spiders_conf.iteritems():
        common = conf['common']
        each = conf['each']
        for _each in each:
            to_append = merge_dict(common, _each)
            lottery_info = to_append['lottery_info']
            lottery_info.setdefault('period', lottery_period.get(lottery_info['key']))
            ret.setdefault(spidercls, []).append(to_append)
    return ret


if __name__ == '__main__':
    from pprint import pprint
    pprint(get_all())
