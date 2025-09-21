# -*- coding: utf-8 -*-

import base64
import json
import requests

from odoo import fields, models, _
from odoo.exceptions import UserError, Warning

from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm


class AccountMove(models.Model):
    _inherit = 'account.move'

    cfdi_emitter_company_id = fields.Many2one(
        'res.company',
        string='Compañía CFDI',
        copy=False,
        help='Compañía que se utilizará como emisor al generar el CFDI.'
    )

    def _get_cfdi_emitter_company(self):
        self.ensure_one()
        return self.cfdi_emitter_company_id or self.company_id

    def action_cfdi_generate(self):
        if not self.env.context.get('skip_cfdi_multi_company'):
            self.ensure_one()
            emitter = self.cfdi_emitter_company_id or self.company_id
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_move_id': self.id,
                'default_company_id': emitter.id,
            })
            return {
                'name': _('Seleccionar compañía CFDI'),
                'type': 'ir.actions.act_window',
                'res_model': 'cfdi.multi.company.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': ctx,
            }

        emitter_id = self.env.context.get('cfdi_force_company_id')
        if emitter_id:
            self.write({'cfdi_emitter_company_id': emitter_id})

        return self._action_cfdi_generate_multi_company()

    def _action_cfdi_generate_multi_company(self):
        for invoice in self:
            emitter = invoice._get_cfdi_emitter_company()
            if invoice.proceso_timbrado:
                raise UserError(_(
                    'El intento de timbrado previo terminó con un error, revise que todo esté correcto o envíe el código de error para su revisión. '\
                    'Si requiere timbrar la factura nuevamente deshabilite el checkbox de "Proceso de timbrado" de la pestaña CFDI.'
                ))
            else:
                invoice.write({'proceso_timbrado': True})
                self.env.cr.commit()
            if invoice.estado_factura == 'factura_correcta':
                if invoice.folio_fiscal:
                    invoice.write({'factura_cfdi': True})
                    return True
                else:
                    invoice.write({'proceso_timbrado': False})
                    self.env.cr.commit()
                    raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if invoice.estado_factura == 'factura_cancelada':
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))

            values = invoice.to_json()
            if emitter.proveedor_timbrado == 'servidor':
                url = 'https://facturacion.itadmin.com.mx/api/invoice'
            elif emitter.proveedor_timbrado == 'servidor2':
                url = 'https://facturacion2.itadmin.com.mx/api/invoice'
            else:
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('Error, falta seleccionar el servidor de timbrado en la configuración de la compañía emisora.'))

            try:
                response = requests.post(
                    url,
                    auth=None,
                    data=json.dumps(values),
                    headers={"Content-type": "application/json"}
                )
            except Exception as e:
                error = str(e)
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                if "Name or service not known" in error or "Failed to establish a new connection" in error:
                    raise Warning("No se pudo conectar con el servidor.")
                else:
                    raise Warning(error)

            if "Whoops, looks like something went wrong." in response.text:
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise Warning(
                    "Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas."
                )
            else:
                json_response = response.json()
            estado_factura = json_response['estado_factura']
            if estado_factura == 'problemas_factura':
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_(json_response['problemas_message']))
            if json_response.get('factura_xml'):
                invoice._set_data_from_xml(base64.b64decode(json_response['factura_xml']))
                file_name = invoice.name.replace('/', '_') + '.xml'
                self.env['ir.attachment'].sudo().create({
                    'name': file_name,
                    'datas': json_response['factura_xml'],
                    'res_model': self._name,
                    'res_id': invoice.id,
                    'type': 'binary'
                })

            invoice.write({
                'estado_factura': estado_factura,
                'factura_cfdi': True,
                'proceso_timbrado': False
            })
            invoice.message_post(body="CFDI emitido")
        return True

    def to_json(self):
        self.ensure_one()
        result = super().to_json()
        emitter = self._get_cfdi_emitter_company()
        factura = result.get('factura', {})
        factura.update({
            'serie': self.journal_id.serie_diario or emitter.serie_factura,
            'LugarExpedicion': self.journal_id.codigo_postal or emitter.zip,
        })
        result['factura'] = factura
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
        return result

    def check_cfdi_values(self):
        for move in self:
            emitter = move._get_cfdi_emitter_company()
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

    def _set_data_from_xml(self, xml_invoice):
        self.ensure_one()
        res = super()._set_data_from_xml(xml_invoice)
        if not xml_invoice:
            return res
        emitter = self._get_cfdi_emitter_company()
        options = {'width': 275 * mm, 'height': 275 * mm}
        amount_str = str(self.amount_total).split('.')
        qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (
            self.folio_fiscal,
            (emitter.vat or ''),
            self.partner_id.vat,
            amount_str[0].zfill(10),
            amount_str[1].ljust(6, '0'),
            self.selo_digital_cdfi[-8:],
        )
        self.qr_value = qr_value
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        self.qrcode_image = base64.encodebytes(ret_val.asString('jpg'))
        return res
