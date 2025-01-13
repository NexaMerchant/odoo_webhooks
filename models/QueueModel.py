# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging
from requests import Request, Session
import json
from requests.exceptions import RequestException, HTTPError
from json import JSONEncoder
import base64
import datetime
from rq import Queue
from redis import Redis
# use odoo tools read config
from odoo.tools import config

_logger = logging.getLogger(__name__)

redis_host = config.get('redis_host')
redis_port = config.get('redis_port')
redis_password = config.get('redis_password')
redis_db = config.get('redis_db')

class QueueModel(models.Model):
    _name = 'webhooks.queue'
    _description = 'Queue Model'

    name = fields.Char(string='Name', required=True)
    url = fields.Char(string='URL', required=True)
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ], string='Method', required=True, default='GET')
    headers = fields.Text(string='Headers', required=False)
    body = fields.Text(string='Body', required=False)
    response = fields.Text(string='Response', required=False)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', required=True, default='pending')
    active = fields.Boolean(string='Active', default=True)

    def send_request(self):
        for record in self:
            if record.active:
                if record.method == 'GET':
                    try:
                        response = requests.get(record.url, headers=json.loads(record.headers))
                        record.response = response.text
                        record.status = 'success'
                    except RequestException as e:
                        record.response = str(e)
                        record.status = 'failed'
                elif record.method == 'POST':
                    try:
                        response = requests.post(record.url, headers=json.loads(record.headers), data=json.loads(record.body))
                        record.response = response.text
                        record.status = 'success'
                    except RequestException as e:
                        record.response = str(e)
                        record.status = 'failed'
                elif record.method == 'PUT':
                    try:
                        response = requests.put(record.url, headers=json.loads(record.headers), data=json.loads(record.body))
                        record.response = response.text
                        record.status = 'success'
                    except RequestException as e:
                        record.response = str(e)
                        record.status = 'failed'
                elif record.method == 'DELETE':
                    try:
                        response = requests.delete(record.url, headers=json.loads(record.headers))
                        record.response = response.text
                        record.status = 'success'
                    except RequestException as e:
                        record.response = str(e)
                        record.status = 'failed'
    # send request async
    def send_request_async(self):
        for record in self:
            if record.active:
                q = Queue(connection=Redis(redis_host, redis_port, redis_password, redis_db))
                job = q.enqueue('webhooks.models.QueueModel.send_request', record.id)
                _logger.info('Job ID: %s' % job.id)
                return job.id
            else:
                return False
    # get job status by id        
    def get_job_status(self, job_id):
        # redis need add 127.0.0.1 and user password
        q = Queue(connection=Redis(redis_host, redis_port, redis_password, redis_db))
        job = q.fetch_job(job_id)
        return job.get_status()
    # get job result by id
    def get_job_result(self, job_id):
        q = Queue(connection=Redis(redis_host, redis_port, redis_password, redis_db))
        job = q.fetch_job(job_id)
        return job.result
    # get job by id
    def get_job(self, job_id):
        q = Queue(connection=Redis(redis_host, redis_port, redis_password, redis_db))
        job = q.fetch_job(job_id)
        return job

    