#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import requests
from gSpider.http.request import Request
from gSpider.http.response import Response


class ExecutionEngine(object):

    def __init__(self, crawler, spider_closed_callback):
        self.crawler = crawler
        self.settings = crawler.settings
        self.spider = None
        self.running = False

    def open_spider(self, spider, start_requests=(), close_if_idle=True):
        print start_requests
        for each in start_requests:
            self._handle_request(each)

    # TODO: scraper
    def _handle_request(self, request):
        response = self._download(request)
        callback = request.callback
        if callback and response.status == 200:
            ret = callback(response)
            if ret:
                for each in ret:
                    if isinstance(each, Request):
                        self._handle_request(each)
                    elif isinstance(each, dict):
                        pass
                    elif each is None:
                        pass
                    else:
                        raise TypeError('should be request or dict')

    # TODO: downloader
    def _download(self, request):
        method = request.method
        s = requests.Session()
        s.keep_alive = False
        try:
            if method == 'GET':
                # r = requests.get(request.url, headers=request.headers)
                r = s.get(request.url, headers=request.headers)
            elif method == 'POST':
                # r = requests.post(request.url, headers=request.headers, data=request.body)
                r = s.post(request.url, headers=request.headers, data=request.body)
            else:
                raise ValueError('method not get or post')
            return Response(r.url, body=r.text)
        except Exception:
            print(traceback.format_exc())
            return Response(request.url, status=1000)
