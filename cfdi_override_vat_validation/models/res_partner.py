from odoo import api, models


class ResPartner(models.Model):
    """Disable VAT/RFC validation for partners."""

    _inherit = 'res.partner'

    @api.constrains('vat')
    def check_vat(self):
        """Override to bypass all VAT validations."""
        for _partner in self:
            # Purposefully do nothing to skip parent validation
            pass
