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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

_logger = logging.getLogger(__name__)

class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class webhooks(models.Model):
    _name = 'webhooks.webhooks'
    _description = 'webhooks.webhooks'

    name = fields.Char(string='Name', required=True)
    website_id = fields.Many2one('website', string='Website') 
    url = fields.Char(string='Webhook URL', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', string='Model Name')
    secert_key = fields.Char(string='Secert Key')
    trigger_on_create = fields.Boolean(string='Trigger on Create', default=True)
    trigger_on_write = fields.Boolean(string='Trigger on Write', default=True )
    trigger_on_delete = fields.Boolean(string='Trigger on Delete', default=True)
    last_call = fields.Datetime(string='Last Called')

    # use queue job to send webhook
    # use cron job to send webhook
    def _send_webhook(self, record, action):
        print(f'Sending webhook to {self.url}')
        if not self.is_active:
            return
        if action == 'create' and not self.trigger_on_create:
            return
        if action == 'write' and not self.trigger_on_write:
            return
        # add delete trigger
        if action == 'unlink' and not self.trigger_on_delete:
            return
        # if the webhook has website_id, check if the record belongs to the website
        if record.website_id and self.website_id and record.website_id != self.website_id:
            return
        try:

            # Convert record data to json
            try:
                record_data = record.read()[0]
                for key, value in record_data.items():
                    if isinstance(value, bytes):
                        record_data[key] = value.decode('utf-8')
                    elif isinstance(value, datetime.datetime):
                        record_data[key] = value.isoformat()
                # when model eq product.product, add product variant and product option value  
            except IndexError:
                record_data = record.read()
            except Exception as e:
                _logger.error(f'Webhook failed: {str(e)}')
                raise
                          
            print(record_data)
            values = record_data

            print(values)
            
            data = {
                'action': action,
                'model': self.model_id.model,
                'record_id': record.id,
                'values': values
            }

            # print(data)

            # print(f'Sending webhook to {self.url}')
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Odoo-Webhook/1.0'
            }

            # When user set secert key, add it to headers
            if self.secert_key:
                headers['Secert-Key'] = self.secert_key

            # print(headers)
            try:
                session = requests.Session()
                session.verify = True
                response = session.post(
                    url=self.url.strip(),
                    json=data,
                    headers=headers,
                    timeout=10,
                    verify=True
                )
                response.raise_for_status()
                
                self.write({
                    'last_call': fields.Datetime.now()
                })
            except HTTPError as http_err:
                _logger.error(f'HTTP error occurred: {http_err}')
                raise
            except RequestException as e:
                _logger.error(f'Webhook request failed: {str(e)}')
                raise
            except Exception as e:
                _logger.error(f'Webhook failed: {self.url} - Error: {str(e)}')
                raise
            _logger.info(f'Webhook sent: {self.url} - Status: {response.status_code}')
        except RequestException as e:
            _logger.error(f'Webhook request failed: {str(e)}')
            raise 
        except Exception as e:
            _logger.error(f'Webhook failed: {self.url} - Error: {str(e)}')
            raise

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    #@api.model
    def write(self, vals):
        try:
            res = super(SaleOrder, self).write(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'write')
                # add it to Queue
                webhook.send_request_async()
            return res
        except Exception as e:
            _logger.error(f'Webhook write sale order failed: {str(e)}')
            raise
    #@api.model
    def create(self, vals):
        try:
            res = super(SaleOrder, self).create(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order')])
            for webhook in webhooks:
                webhook._send_webhook(res, 'create')
            return res
        except Exception as e:
            _logger.error(f'Webhook create sale order failed: {str(e)}')
            raise
    #@api.model
    def unlink(self):
        try:
            res = super(SaleOrder, self).unlink()
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order')])
            print(webhooks)
            for webhook in webhooks:
                webhook._send_webhook(self, 'unlink')
            return res
        except Exception as e:
            _logger.error(f'Webhook unlink sale order failed: {str(e)}')
            raise

# Sale Order Delivery create and update
class SaleOrderDelivery(models.Model):
    _inherit = 'stock.picking'

    def write(self, vals):
        try:
            res = super(SaleOrderDelivery, self).write(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'stock.picking')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'write')
            return res
        except Exception as e:
            _logger.error(f'Webhook write sale order delivery failed: {str(e)}')
            raise

    def create(self, vals):
        try:
            res = super(SaleOrderDelivery, self).create(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'stock.picking')])
            for webhook in webhooks:
                webhook._send_webhook(res, 'create')
            return res
        except Exception as e:
            _logger.error(f'Webhook create sale order delivery failed: {str(e)}')
            raise
    def unlink(self):
        try:
            res = super(SaleOrderDelivery, self).unlink()
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'stock.picking')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'unlink')
            return res
        except Exception as e:
            _logger.error(f'Webhook unlink sale order delivery failed: {str(e)}')
            raise

    
# Sale Order Line Update, create and delete
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    #@api.model
    def write(self, vals):
        try:
            res = super(SaleOrderLine, self).write(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order.line')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'write')
            return res
        except Exception as e:
            _logger.error(f'Webhook write sale order line failed: {str(e)}')
            raise
    #@api.model
    def create(self, vals):
        try:
            res = super(SaleOrderLine, self).create(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order.line')])
            for webhook in webhooks:
                webhook._send_webhook(res, 'create')
            return res
        except Exception as e:
            _logger.error(f'Webhook create sale order line failed: {str(e)}')
            raise
    #@api.model
    def unlink(self):
        try:
            res = super(SaleOrderLine, self).unlink()
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order.line')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'unlink')
            return res
        except Exception as e:
            _logger.error(f'Webhook unlink sale order line failed: {str(e)}')
            raise

#Product Update and create
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    #@api.model
    def write(self, vals):
        try:
            res = super(ProductTemplate, self).write(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.template')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'write')
            return res
        except Exception as e:
            _logger.error(f'Webhook write product template failed: {str(e)}')
            raise
    
    #@api.model
    def create(self, vals):
        try:
            res = super(ProductTemplate, self).create(vals)
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.template')])
            for webhook in webhooks:
                webhook._send_webhook(res, 'create')
            return res
        except Exception as e:
            _logger.error(f'Webhook create product template failed: {str(e)}')
            raise
    #@api.model
    def unlink(self):
        try:
            res = super(ProductTemplate, self).unlink()
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.template')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'unlink')
            return res
        except Exception as e:
            _logger.error(f'Webhook unlink product template failed: {str(e)}')
            raise
    
# Product Update and create
class ProductProduct(models.Model):
    _inherit = 'product.product'

    #@api.model
    def write(self, vals):
        try:
            res = super(ProductProduct, self).write(vals)
            product = self.env['product.template'].search([('product_variant_id', '=', self.id)])
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.product')])
            for webhook in webhooks:
                webhook._send_webhook(self, product, 'write')
            return res
        except Exception as e:
            _logger.error(f'Webhook write product product failed: {str(e)}')
            raise
    #@api.model
    def create(self, vals):
        try:
            res = super(ProductProduct, self).create(vals)
            # format product data to json
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.product')])
            for webhook in webhooks:
                webhook._send_webhook(res, 'create')
            return res
        except Exception as e:
            _logger.error(f'Webhook create product product failed: {str(e)}')
            raise
    #@api.model
    def unlink(self):
        try:
            res = super(ProductProduct, self).unlink()
            webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.product')])
            for webhook in webhooks:
                webhook._send_webhook(self, 'unlink')
            return res
        except Exception as e:
            _logger.error(f'Webhook unlink product product failed: {str(e)}')
            raise
