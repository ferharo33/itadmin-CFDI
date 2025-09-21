# -*- coding: utf-8 -*-
##############################################################################
#                 @author IT admin
#
##############################################################################

{
    'name': 'Timbrado de facturas con multiples RFC',
    'version': '14.1',
    'description': ''' Permite a una sola compañía timbrar facturas con multiples RFC's
    ''',
    'category': 'Accounting',
    'author': 'Teamfactory',
    'website': 'teamfactory.cloud',
    'depends': [
        'base','sale', 'cdfi_invoice',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'report/invoice_report.xml',
    ],
    'application': False,
    'installable': True,
}
