#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from lottery import format_issue, RULES


spring_fes = {
    "2011": "02-02",
    "2012": "01-22",
    "2013": "02-10",
    "2014": "01-30",
    "2015": "02-18",
    "2016": "02-07",
    "2017": "01-27",
    "2018": "02-15",
    "2019": "02-04",
    "2020": "01-24",
}


def get_ymd_b(issue):
    length = len(issue)
    rule = RULES['l' + str(length)]
    al = rule['al']
    bl = rule['bl']
    if al == 2 or al == 4:
        return int(issue[:al]), None, None, int(issue[-bl:])
    if al == 6:
        return int(issue[:2]), int(issue[2:4]), int(issue[4:6]), int(issue[6:])
    if al == 8:
        return int(issue[:4]), int(issue[4:6]), int(issue[6:8]), int(issue[8:])


def if_date(*args):
    try:
        args = map(int, args)
        datetime(*args)
        return True
    except Exception:
        return False


# 只针对高频彩有效
class IssueChecker(object):

    # continuous是为了做check的例外处理，在这区间的都认为是连续的
    def __init__(self, reverse=True, mode='normal', issue_range=None, issue_length=None, b_hm=None, continuous=None):
        self.reverse = reverse
        self.continuous = self._set_continuous(continuous)

        self.mode = mode
        if self.mode == 'abnormal':
            pass
        elif self.mode == 'normal':
            self.issue_range = issue_range
            self.issue_length = issue_length
            if self.issue_length:
                self._set()
            self.b_hm = b_hm

    def _set(self):
        self.rule = RULES['l' + str(self.issue_length)]
        self.al = self.rule['al']
        self.bl = self.rule['bl']

    @staticmethod
    def _set_continuous(continuous):
        if not continuous:
            return None
        ret = []
        for each in continuous:
            if '~~' in each:
                each = map(lambda _: _.strip(), each.split('~~'))
                ret.append(each)
        return ret

    @property
    def _escape_range(self):
        if not hasattr(self, '__escape_range'):
            self.__escape_range = []
            for idx in range(len(self.issue_range) - 1):
                start = self.issue_range[idx][0].split('~~')[1]
                end = self.issue_range[idx + 1][0].split('~~')[0]
                start = datetime.strptime(start, '%Y-%m-%d') + timedelta(days=1)
                end = datetime.strptime(end, '%Y-%m-%d')
                self.__escape_range.append((start, end))

            # 添加春节期间的escape_range
            min_start = self.__escape_range[0][0]
            max_end = self.__escape_range[-1][-1]
            for year in spring_fes:
                start = datetime.strptime(year + '-' + spring_fes[year], '%Y-%m-%d')
                end = start + timedelta(days=7)
                if end < min_start:
                    self.__escape_range.insert(0, (start, end))
                elif start > max_end:
                    self.__escape_range.append((start, end))
        return self.__escape_range

    def _if_max_b(self, issue):
        max_issue = self._get_min_max(*self._ymd(issue))[-1]
        if int(issue[-self.bl:]) == max_issue:
            return True
        return False

    def _get_min_max(self, y, m, d):
        ymd = '%d-%02d-%02d' % (y, m, d)
        for ymd_s, max_b in self.issue_range:
            l, r = ymd_s.split('~~')
            if l and ymd < l:
                continue
            if r and ymd > r:
                continue
            return 1, max_b
        # 如果在上述范围以外, 用最新的期号范围
        return 1, max_b

    def _if_min_b(self, issue):
        # min_issue = self._get_min_max(issue)[0]
        min_issue = 1
        if int(issue[-self.bl:]) == min_issue:
            return True
        return False

    # 检查issue2 是不是issue1 的上一期或是下一期
    def check(self, issue1, issue2):
        try:
            if self.reverse and int(issue1) - int(issue2) == 1 or not self.reverse and int(issue2) - int(issue1) == 1:
                return True
            if self.reverse and issue1 < issue2 or not self.reverse and issue2 < issue1:
                return False
        except ValueError:
            return False
        iterable = self.iter_by_issue(issue1)
        next(iterable)  # issue1
        the_next = next(iterable)
        if the_next == issue2:
            return True
        if self.__in_continuous(issue1, issue2):
            return True
        return False

    # 在某个区间的issue被认为是连续，因为有些issue可能确实没有数据
    def __in_continuous(self, issue1, issue2):
        if not self.continuous:
            return False
        for issue in [issue1, issue2]:
            for l, r in self.continuous:
                if l and issue < l:
                    return False
                if r and issue > r:
                    return False
        return True

    def _get_pre_date(self, issue):
        year, month, day = self._ymd(issue)
        pre_date = datetime(year, month, day) - timedelta(days=1)
        escape = self._if_escape(pre_date)
        if escape:
            pre_date = escape[0] - timedelta(days=1)
        return pre_date

    def _get_next_date(self, issue):
        year, month, day = self._ymd(issue)
        next_date = datetime(year, month, day) + timedelta(days=1)
        escape = self._if_escape(next_date)
        if escape:
            next_date = escape[1]
        return next_date

    def _if_escape(self, date):
        for each in self._escape_range:
            if date >= each[0] and date < each[1]:
                return each

    def _ymd(self, issue):
        if self.al == 6:
            year, month, day = int(issue[:2]), int(issue[2:4]), int(issue[4:6])
            # 1980-2079
            if year >= 80:
                year += 1900
            else:
                year += 2000
        elif self.al == 8:
            year, month, day = int(issue[:4]), int(issue[4:6]), int(issue[6:8])
        return year, month, day

    def _b(self, issue):
        return int(issue[-self.bl:])

    def _ymd_b_to_issue(self, y, m, d, b):
        y = str(y)[-2:] if self.al == 6 else str(y)
        if self.bl == 2:
            return '%s%02d%02d%02d' % (y, m, d, b)
        if self.bl == 3:
            return '%s%02d%02d%03d' % (y, m, d, b)

    def iter_by_issue(self, issue):
        if self.mode == 'normal':
            if not self.issue_length:
                self.issue_length = len(issue)
                self._set()
            if len(issue) != self.issue_length:
                issue = format_issue(issue, self.issue_length)
            cur_issue = issue
            yield cur_issue
            get_date = self._get_pre_date if self.reverse else self._get_next_date
            if_max_min = self._if_min_b if self.reverse else self._if_max_b
            fmt = '%0' + str(self.issue_length) + 'd'
            if self.reverse:
                change = lambda cur_issue: fmt % (int(cur_issue) - 1)
            else:
                change = lambda cur_issue: fmt % (int(cur_issue) + 1)
            idx = 1 if self.reverse else 0
            while True:
                if if_max_min(cur_issue):
                    date = get_date(cur_issue)
                    y, m, d = date.year, date.month, date.day
                    b = self._get_min_max(y, m, d)[idx]
                    cur_issue = self._ymd_b_to_issue(y, m, d, b)
                    yield cur_issue
                else:
                    cur_issue = change(cur_issue)
                    yield cur_issue
        else:
            self.issue_length = len(issue)
            cur_issue = issue
            yield cur_issue
            fmt = '%0' + str(self.issue_length) + 'd'
            if self.reverse:
                change = lambda cur_issue: fmt % (int(cur_issue) - 1)
            else:
                change = lambda cur_issue: fmt % (int(cur_issue) + 1)
            while True:
                cur_issue = change(cur_issue)
                yield cur_issue

    def _open_time_of_issue(self, issue):
        hm = None
        in_next_day = False
        if self.b_hm:
            hm = self.b_hm.get(str(int(issue[-self.bl:])))
            if hm:
                if '+' in hm:
                    in_next_day = True
                    hm = hm.replace('+', '')
                hm = ' ' + hm
        y, m, d = self._get_next_date(issue) if in_next_day else self._ymd(issue)
        ret = '%04d-%02d-%02d' % (y, m, d)
        if hm is not None:
            ret += hm
        return ret

    def iter_by_issue_with_open_time(self, issue):
        if self.mode != 'normal':
            raise NotImplemented('this method is for normal mode')
        iterable = self.iter_by_issue(issue)
        while True:
            each = next(iterable)
            yield each, self._open_time_of_issue(each)
