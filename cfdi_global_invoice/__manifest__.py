# -*- coding: utf-8 -*-
{
    'name': 'CFDI Factura Global',
    'version': '14.1',
    'summary': 'Generación de facturas globales desde múltiples pedidos de venta',
    'description': """
        Módulo para crear facturas globales CFDI
        ==========================================

        Permite seleccionar múltiples pedidos de venta y generar una sola factura,
        agrupando productos y sumando cantidades con precio promedio ponderado.

        Características:
        - Selección múltiple de pedidos de venta
        - Agrupación de productos
        - Cálculo de precio promedio ponderado
        - Validación de moneda única
        - Trazabilidad completa
    """,
    'author': 'Teamfactory',
    'website': 'https://teamfactory.mx',
    'category': 'Sales',
    'depends': ['base', 'sale', 'account', 'cdfi_invoice'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_create_global_invoice_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
