# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict


class SaleCreateGlobalInvoice(models.TransientModel):
    _name = 'sale.create.global.invoice'
    _description = 'Crear Factura Global desde Múltiples Pedidos'

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        help='Cliente para la factura global'
    )

    date_invoice = fields.Date(
        string='Fecha de Factura',
        default=fields.Date.context_today,
        required=True
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        required=True,
        domain=[('type', '=', 'sale')],
        help='Diario de ventas para la factura'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        compute='_compute_currency_id',
        readonly=True
    )

    sale_order_count = fields.Integer(
        string='Número de Pedidos',
        compute='_compute_sale_order_count'
    )

    @api.depends('partner_id')
    def _compute_currency_id(self):
        """Obtiene la moneda de los pedidos seleccionados"""
        for wizard in self:
            sale_orders = self._get_sale_orders()
            if sale_orders:
                wizard.currency_id = sale_orders[0].currency_id
            else:
                wizard.currency_id = self.env.company.currency_id

    def _compute_sale_order_count(self):
        """Cuenta los pedidos seleccionados"""
        for wizard in self:
            wizard.sale_order_count = len(self._get_sale_orders())

    @api.model
    def default_get(self, fields_list):
        """Establece valores por defecto del wizard"""
        res = super(SaleCreateGlobalInvoice, self).default_get(fields_list)

        # Obtener el diario de ventas por defecto
        if 'journal_id' in fields_list:
            journal = self.env['account.journal'].search(
                [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)],
                limit=1
            )
            if journal:
                res['journal_id'] = journal.id

        # Obtener cliente por defecto de configuración o del primer pedido
        if 'partner_id' in fields_list:
            sale_orders = self._get_sale_orders()
            if sale_orders:
                # Usar el cliente del primer pedido como sugerencia
                res['partner_id'] = sale_orders[0].partner_id.id

        return res

    def _get_sale_orders(self):
        """Obtiene los pedidos de venta desde el contexto"""
        sale_order_ids = self.env.context.get('active_ids', [])
        return self.env['sale.order'].browse(sale_order_ids)

    def _validate_sale_orders(self, sale_orders):
        """Valida que los pedidos cumplan los requisitos para factura global"""
        if not sale_orders:
            raise UserError(_('No se han seleccionado pedidos de venta.'))

        # Verificar que estén confirmados
        invalid_states = sale_orders.filtered(lambda so: so.state not in ('sale', 'done'))
        if invalid_states:
            raise UserError(_(
                'Los siguientes pedidos no están confirmados:\n%s'
            ) % '\n'.join(invalid_states.mapped('name')))

        # Verificar que no estén facturados
        already_invoiced = sale_orders.filtered(lambda so: so.invoice_status == 'invoiced')
        if already_invoiced:
            raise UserError(_(
                'Los siguientes pedidos ya están facturados:\n%s'
            ) % '\n'.join(already_invoiced.mapped('name')))

        # Verificar que tengan la misma moneda
        currencies = sale_orders.mapped('currency_id')
        if len(currencies) > 1:
            raise UserError(_(
                'Todos los pedidos deben tener la misma moneda.\n'
                'Monedas encontradas: %s'
            ) % ', '.join(currencies.mapped('name')))

        # Verificar que tengan líneas facturables
        orders_without_lines = sale_orders.filtered(
            lambda so: not so.order_line.filtered(lambda l: not l.display_type)
        )
        if orders_without_lines:
            raise UserError(_(
                'Los siguientes pedidos no tienen líneas facturables:\n%s'
            ) % '\n'.join(orders_without_lines.mapped('name')))

        return True

    def _group_lines_by_product(self, sale_orders):
        """
        Agrupa líneas por producto, suma cantidades y calcula precio promedio ponderado

        Returns:
            list: Lista de diccionarios con datos de líneas agrupadas
        """
        grouped_lines = defaultdict(lambda: {
            'product_id': False,
            'quantity': 0.0,
            'weighted_price': 0.0,
            'weighted_discount': 0.0,
            'price_unit': 0.0,
            'discount': 0.0,
            'tax_ids': False,
            'product_uom': False,
            'sale_lines': self.env['sale.order.line'],
            'name': '',
        })

        # Recopilar todas las líneas facturables
        for order in sale_orders:
            for line in order.order_line.filtered(lambda l: not l.display_type):
                product_id = line.product_id.id

                # Acumular cantidad y precios ponderados
                grouped_lines[product_id]['product_id'] = line.product_id
                grouped_lines[product_id]['quantity'] += line.product_uom_qty
                grouped_lines[product_id]['weighted_price'] += (line.price_unit * line.product_uom_qty)
                grouped_lines[product_id]['weighted_discount'] += (line.discount * line.product_uom_qty)
                grouped_lines[product_id]['sale_lines'] |= line

                # Mantener valores del primer registro encontrado
                if not grouped_lines[product_id]['tax_ids']:
                    grouped_lines[product_id]['tax_ids'] = line.tax_id
                    grouped_lines[product_id]['product_uom'] = line.product_uom
                    grouped_lines[product_id]['name'] = line.name

        # Calcular promedios ponderados
        result = []
        for product_id, data in grouped_lines.items():
            if data['quantity'] > 0:
                data['price_unit'] = data['weighted_price'] / data['quantity']
                data['discount'] = data['weighted_discount'] / data['quantity']

            result.append(data)

        return result

    def _prepare_global_invoice_values(self, sale_orders, grouped_lines):
        """
        Prepara los valores para crear la factura global

        Args:
            sale_orders: Recordset de pedidos de venta
            grouped_lines: Lista de líneas agrupadas

        Returns:
            dict: Valores para account.move.create()
        """
        # Preparar líneas de factura
        invoice_line_values = []
        for line_data in grouped_lines:
            invoice_line_values.append((0, 0, {
                'product_id': line_data['product_id'].id,
                'name': line_data['name'],
                'quantity': line_data['quantity'],
                'price_unit': line_data['price_unit'],
                'discount': line_data['discount'],
                'product_uom_id': line_data['product_uom'].id,
                'tax_ids': [(6, 0, line_data['tax_ids'].ids)],
                'sale_line_ids': [(6, 0, line_data['sale_lines'].ids)],
            }))

        # Preparar valores base de la factura
        invoice_values = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': self.date_invoice,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'invoice_origin': ', '.join(sale_orders.mapped('name')),
            'invoice_line_ids': invoice_line_values,
        }

        # Agregar campos CFDI si están disponibles en el modelo
        AccountMove = self.env['account.move']
        if hasattr(AccountMove, 'tipo_comprobante'):
            invoice_values.update({
                'tipo_comprobante': 'I',  # Ingreso
            })

        if hasattr(AccountMove, 'uso_cfdi'):
            # Intentar obtener uso_cfdi del cliente
            if self.partner_id.uso_cfdi:
                invoice_values['uso_cfdi'] = self.partner_id.uso_cfdi.id

        if hasattr(AccountMove, 'metodo_pago'):
            invoice_values['metodo_pago'] = 'PUE'  # Pago en una sola exhibición

        if hasattr(AccountMove, 'forma_pago'):
            # Intentar obtener forma de pago del cliente
            if hasattr(self.partner_id, 'forma_pago') and self.partner_id.forma_pago:
                invoice_values['forma_pago'] = self.partner_id.forma_pago.id

        return invoice_values

    def _mark_orders_as_invoiced(self, sale_orders, invoice):
        """
        Marca los pedidos como facturados y establece la trazabilidad

        Args:
            sale_orders: Recordset de pedidos de venta
            invoice: Factura creada
        """
        # Marcar campos de trazabilidad en los pedidos
        sale_orders.write({
            'is_global_invoice': True,
            'global_invoice_id': invoice.id,
        })

        # Registrar mensaje en cada pedido
        for order in sale_orders:
            order.message_post(
                body=_('Incluido en factura global: %s') % invoice.name
            )

        # Registrar mensaje en la factura
        invoice.message_post(
            body=_('Factura global creada desde los pedidos: %s') % ', '.join(
                sale_orders.mapped('name')
            )
        )

    def create_global_invoice(self):
        """
        Método principal que crea la factura global

        Returns:
            dict: Acción para abrir la factura creada
        """
        self.ensure_one()

        # Obtener y validar pedidos
        sale_orders = self._get_sale_orders()
        self._validate_sale_orders(sale_orders)

        # Agrupar líneas por producto
        grouped_lines = self._group_lines_by_product(sale_orders)

        # Preparar valores de factura
        invoice_values = self._prepare_global_invoice_values(sale_orders, grouped_lines)

        # Crear factura
        invoice = self.env['account.move'].create(invoice_values)

        # Marcar pedidos como facturados
        self._mark_orders_as_invoiced(sale_orders, invoice)

        # Retornar acción para abrir la factura
        return {
            'name': _('Factura Global'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
