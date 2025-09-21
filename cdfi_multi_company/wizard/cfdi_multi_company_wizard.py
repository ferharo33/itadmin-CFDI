# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class CdfiMultiCompanyWizard(models.TransientModel):
    _name = 'cfdi.multi.company.wizard'
    _description = 'Seleccionar compañía emisora CFDI'

    move_id = fields.Many2one('account.move', string='Factura', required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía emisora', required=True)

    def action_confirm(self):
        self.ensure_one()
        move = self.move_id
        if not move:
            raise UserError(_('No se encontró la factura a timbrar.'))
        emitter = self.company_id
        if not emitter:
            raise UserError(_('Debe seleccionar una compañía emisora.'))
        ctx = dict(self.env.context or {})
        ctx.update({
            'skip_cfdi_multi_company': True,
            'cfdi_force_company_id': emitter.id,
        })
        return move.with_context(ctx).action_cfdi_generate()
