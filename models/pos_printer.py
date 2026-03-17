# -*- coding: utf-8 -*-
import socket
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPrinter(models.Model):
    _inherit = 'pos.printer'

    printer_type = fields.Selection(
        selection_add=[('escpos_local', 'ESC/POS Network Printer (Local)')]
    )
    escpos_local_ip = fields.Char(
        string='Printer IP Address',
        help='IP address of the ESC/POS network printer (e.g. 192.168.1.101)',
        default='0.0.0.0',
    )
    escpos_local_port = fields.Integer(
        string='Printer Port',
        default=9100,
    )

    @api.constrains('escpos_local_ip')
    def _check_escpos_local_ip(self):
        for record in self:
            if record.printer_type == 'escpos_local' and not record.escpos_local_ip:
                raise UserError(_('Printer IP Address cannot be empty.'))

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['escpos_local_ip', 'escpos_local_port']
        return params

    def action_test_printer_connection(self):
        """Test TCP connection to ESC/POS printer."""
        self.ensure_one()
        if self.printer_type != 'escpos_local':
            raise UserError(_('This action is only for ESC/POS Network Printer (Local).'))
        if not self.escpos_local_ip:
            raise UserError(_('Please enter the printer IP address first.'))

        ip   = self.escpos_local_ip.strip()
        port = self.escpos_local_port or 9100
        try:
            sock = socket.create_connection((ip, port), timeout=5)
            sock.close()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title'  : _('Printer Connected ✅'),
                    'message': _('Successfully connected to printer at %s:%s') % (ip, port),
                    'type'   : 'success',
                    'sticky' : False,
                },
            }
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title'  : _('Printer Unreachable ❌'),
                    'message': _('Could not connect to printer at %s:%s — %s') % (ip, port, e),
                    'type'   : 'danger',
                    'sticky' : True,
                },
            }
