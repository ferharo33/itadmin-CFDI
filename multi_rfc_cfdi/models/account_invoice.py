# -*- coding: utf-8 -*-

import base64
import json

from odoo import fields, models, api,_ 


import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    custom_company_id = fields.Many2one('res.company', 'Compañia para CFDI', required=True)

    @api.model
    def to_json(self):
        res = super(AccountInvoice,self).to_json()

        res['company'].update({'rfc': self.custom_company_id.rfc,
                               'api_key': self.custom_company_id.proveedor_timbrado,
                               'modo_prueba': self.custom_company_id.modo_prueba,
                               'regimen_fiscal': self.custom_company_id.regimen_fiscal,
                               'postalcode': self.custom_company_id.zip,
                               'nombre_fiscal': self.custom_company_id.nombre_fiscal,})

        if not self.custom_company_id.archivo_cer:
            raise UserError(_('Archivo .cer path is missing.'))
        if not self.custom_company_id.archivo_key:
            raise UserError(_('Archivo .key path is missing.'))
        archivo_cer = self.custom_company_id.archivo_cer
        archivo_key = self.custom_company_id.archivo_key

        res['certificados'].update({'archivo_cer': archivo_cer.decode("utf-8"),
                               'archivo_key': archivo_key.decode("utf-8"),
                               'contrasena': self.custom_company_id.contrasena,
                               })
        return res

