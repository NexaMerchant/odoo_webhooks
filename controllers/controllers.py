# -*- coding: utf-8 -*-
# from odoo import http


# class Webhooks(http.Controller):
#     @http.route('/webhooks/webhooks', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/webhooks/webhooks/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('webhooks.listing', {
#             'root': '/webhooks/webhooks',
#             'objects': http.request.env['webhooks.webhooks'].search([]),
#         })

#     @http.route('/webhooks/webhooks/objects/<model("webhooks.webhooks"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('webhooks.object', {
#             'object': obj
#         })

