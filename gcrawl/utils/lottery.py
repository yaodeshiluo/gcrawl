#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime

RULES = dict(
    l5=dict(a="%y", al=2, bl=3, c="normal"),
    l7=dict(a="%Y", al=4, bl=3, c="normal"),
    l8=dict(a="%y%m%d", al=6, bl=2, c="high"),
    l9=dict(a="%y%m%d", al=6, bl=3, c="high"),
    l10=dict(a="%Y%m%d", al=8, bl=2, c="high"),
    l11=dict(a="%Y%m%d", al=8, bl=3, c="high"),
)


def gcd(a, b):
    """
    计算最大公约数
    """
    if b == 0:
        return a
    return gcd(b, a % b)


def is_cron(date, cron):
    """
    determine whether it is the time match the value
    value format:
    minute houre day month week
    like:
    1 * * * *

    :returns: True or False

    """
    for value in cron:
        match = True
        sp = value.split()
        if len(sp) != 5:
            continue
        for item in zip(sp, ['minute', 'hour', 'day', 'month', 'week']):
            if not match_one_slot(date, *item):
                match = False
                break
        if not match:
            continue
        else:
            return True
    return False


def match_one_slot(now, value, slot_type):
    """
    called by is_cron
    determine one type of format
    value is a string like '*/5' or '2' or '*'
    slot_type is one of : minute houre day month week
    week: from 0 to 6, 0 is sunday
    """
    n = getattr(now, slot_type) if slot_type != 'week' else ((now.weekday() + 1) % 7)
    for area in value.split(','):
        sp = area.split('/')
        mod = int(sp[1]) if len(sp) > 1 else 1
        mod_start = 0
        pattern = sp[0]
        sp = pattern.split('-')
        rng = []
        if '-' in pattern and len(sp) == 2:
            # case like: 0-59
            rng = range(int(sp[0]), int(sp[1]) + 1)
            mod_start = int(sp[0])
        if pattern in ['*', str(n)] or n in rng:
            # match patter, consider mod
            if (n - mod_start) % mod == 0:
                # all match
                return True
    return False


def format_issue(issue, length):
    """输入issue和想要转换的长度，该函数尝试对其进行转换以符合length要求。如果发现有问题，返回None，没问题返回转换后的issue"""
    now_rule = RULES.get("l%s" % len(issue))
    if not now_rule:
        return None
    target_rule = RULES.get("l%s" % length)
    if not target_rule:
        return None
    if now_rule['c'] != target_rule['c']:
        logging.info("category unmatch, can not change between normal and high freq")
        return None
    now = datetime.datetime.now()
    try:
        a = issue[:now_rule["al"]]
        b = int(issue[now_rule["al"]:])
        if len(a) in (6, 8):
            day = int(a[-2:])
            month = int(a[-4:-2])
            year = int(a[:-4])
        else:
            year = int(a)
            month = now.month
            day = now.day
    except:
        # 不可识别的期号
        import traceback
        print traceback.format_exc()
        return None

    # 期号日期规则检查，日期不可大于当前日期
    _year = year if year > 2000 else 2000 + year
    issue_date = "%04d%02d%02d" % (_year, month, day)
    if issue_date > now.strftime("%Y%m%d"):
        return None

    # 检查完毕，开始转换
    a = a[-target_rule["al"]:]
    if target_rule['al'] - len(a) == 2:
        a = "20" + a
    elif target_rule['al'] != len(a):
        # 理论上不应该到这儿
        logging.info("unexpected a: %s. args: %s, %s" % (a, issue, length))
        return None  # a部分有问题
    b = ("000%s" % b)[-target_rule["bl"]:]

    return a + b
