# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_global_invoice = fields.Boolean(
        string='En Factura Global',
        default=False,
        readonly=True,
        copy=False,
        help='Indica si este pedido está incluido en una factura global'
    )

    global_invoice_id = fields.Many2one(
        'account.move',
        string='Factura Global',
        readonly=True,
        copy=False,
        help='Referencia a la factura global que incluye este pedido'
    )
