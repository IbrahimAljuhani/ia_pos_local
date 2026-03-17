# -*- coding: utf-8 -*-
{
    'name': 'POS Local Terminal & Printer',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Mada payment (NeoLeap) + ESC/POS receipt & kitchen printing for local Odoo servers',
    'description': """
        All-in-one POS module for local Odoo installations (http://).
        No IoT Box or Raspberry Pi required.

        Features:
        - Mada payment via NeoLeap WebSocket (CHECK_STATUS → SALE protocol)
        - Multiple Mada terminals — one IP per payment method
        - ESC/POS receipt printing over TCP (port 9100)
        - Kitchen / order preparation printing over TCP
        - Multiple printers — one IP per printer
        - Test Connection button for each device
        - Bilingual AR/EN messages
    """,
    'author': 'Ibrahim Aljuhani',
    'email': 'info@ia.sa',
    'website': 'https://ia.sa',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/pos_printer_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ia_pos_local/static/src/app/payment_mada.js',
            'ia_pos_local/static/src/app/model.js',
            'ia_pos_local/static/src/app/payment_screen.js',
            'ia_pos_local/static/src/app/printer.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
