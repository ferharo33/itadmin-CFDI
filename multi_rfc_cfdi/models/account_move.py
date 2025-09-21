# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    custom_company_id = fields.Many2one(
        'res.company',
        string='Compañia para CFDI',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía que se utilizará como emisor al generar el CFDI.'
    )

    def _get_cfdi_custom_company(self):
        self.ensure_one()
        return self.custom_company_id or self.company_id

    def to_json(self):
        self.ensure_one()
        result = super().to_json()
        emitter = self._get_cfdi_custom_company()

        if not emitter.archivo_cer:
            raise UserError(_('Archivo .cer path is missing.'))
        if not emitter.archivo_key:
            raise UserError(_('Archivo .key path is missing.'))

        result.setdefault('factura', {})
        result['factura'].update({
            'serie': self.journal_id.serie_diario or emitter.serie_factura,
            'LugarExpedicion': self.journal_id.codigo_postal or emitter.zip,
        })

        nombre_fiscal = (emitter.nombre_fiscal or emitter.name or '').upper()
        result.setdefault('emisor', {})
        result['emisor'].update({
            'rfc': (emitter.vat or '').upper(),
            'nombre': nombre_fiscal,
            'RegimenFiscal': emitter.regimen_fiscal,
        })

        result.setdefault('informacion', {})
        result['informacion'].update({
            'api_key': emitter.proveedor_timbrado,
            'modo_prueba': emitter.modo_prueba,
        })

        result.setdefault('certificados', {})
        result['certificados'].update({
            'archivo_cer': emitter.archivo_cer.decode('utf-8'),
            'archivo_key': emitter.archivo_key.decode('utf-8'),
            'contrasena': emitter.contrasena,
        })
        return result

    def check_cfdi_values(self):
        for move in self:
            emitter = move.custom_company_id or move.company_id
            if not emitter.vat:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El emisor no tiene RFC configurado.'))
            if not (emitter.nombre_fiscal or emitter.name):
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El emisor no tiene nombre configurado.'))
            if not move.partner_id.vat:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El receptor no tiene RFC configurado.'))
            if not move.partner_id.name:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El receptor no tiene nombre configurado.'))
            if not move.uso_cfdi:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('La factura no tiene uso de cfdi configurado.'))
            if not move.tipo_comprobante:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El emisor no tiene tipo de comprobante configurado.'))
            if move.tipo_comprobante != 'T' and not move.methodo_pago:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('La factura no tiene método de pago configurado.'))
            if move.tipo_comprobante != 'T' and not move.forma_pago:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('La factura no tiene forma de pago configurado.'))
            if not emitter.regimen_fiscal:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El emisor no régimen fiscal configurado.'))
            if not move.journal_id.codigo_postal and not emitter.zip:
                move.write({'proceso_timbrado': False})
                move.env.cr.commit()
                raise UserError(_('El emisor no tiene código postal configurado.'))
        return True
