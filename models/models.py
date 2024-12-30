# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class webhooks(models.Model):
    _name = 'webhooks.webhooks'
    _description = 'webhooks.webhooks'

    name = fields.Char(string='Name', required=True)
    website_id = fields.Many2one('website', string='Website') 
    url = fields.Char(string='Webhook URL', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    trigger_on_create = fields.Boolean(string='Trigger on Create', default=True)
    trigger_on_write = fields.Boolean(string='Trigger on Write', default=True)
    trigger_on_delete = fields.Boolean(string='Trigger on Delete', default=True)
    last_call = fields.Datetime(string='Last Called')

    # use queue job to send webhook
    def _send_webhook(self, record, action):
        if not self.is_active:
            return
        if action == 'create' and not self.trigger_on_create:
            return
        if action == 'write' and not self.trigger_on_write:
            return
        # add delete trigger
        if action == 'unlink' and not self.trigger_on_delete:
            return
        try:
            data = {
                'action': action,
                'model': self.model_id.model,
                'record_id': record.id,
                'values': record.read()[0]
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.url,
                data=json.dumps(data),
                headers=headers
            )
            
            self.write({
                'last_call': fields.Datetime.now()
            })
            
            _logger.info(f'Webhook sent: {self.url} - Status: {response.status_code}')
            
        except Exception as e:
            _logger.error(f'Webhook failed: {self.url} - Error: {str(e)}')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order')])
        for webhook in webhooks:
            webhook._send_webhook(self, 'write')
        return res

    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order')])
        for webhook in webhooks:
            webhook._send_webhook(res, 'create')
        return res
    
# Sale Order Line Update, create and delete
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order.line')])
        for webhook in webhooks:
            webhook._send_webhook(self, 'write')
        return res

    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order.line')])
        for webhook in webhooks:
            webhook._send_webhook(res, 'create')
        return res
    
    def unlink(self):
        res = super(SaleOrderLine, self).unlink()
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'sale.order.line')])
        for webhook in webhooks:
            webhook._send_webhook(self, 'unlink')
        return res

#Product Update and create
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.template')])
        for webhook in webhooks:
            webhook._send_webhook(self, 'write')
        return res

    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.template')])
        for webhook in webhooks:
            webhook._send_webhook(res, 'create')
        return res
    
# Product Update and create

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.product')])
        for webhook in webhooks:
            webhook._send_webhook(self, 'write')
        return res

    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        webhooks = self.env['webhooks.webhooks'].search([('model_id.model', '=', 'product.product')])
        for webhook in webhooks:
            webhook._send_webhook(res, 'create')
        return res