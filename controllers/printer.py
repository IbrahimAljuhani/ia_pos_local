# -*- coding: utf-8 -*-
"""
ESC/POS network printer controller.
Odoo server connects to printer over TCP and sends raw ESC/POS data.
"""
import base64
import io
import json
import logging
import socket
import time

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    from escpos.printer import Network as EscposNetwork
    from PIL import Image
    HAS_ESCPOS = True
except ImportError:
    HAS_ESCPOS = False
    _logger.warning(
        'ia_pos_local: python-escpos or Pillow not installed. '
        'Run: pip install python-escpos Pillow'
    )


class PrinterController(http.Controller):

    @http.route('/ia_pos_local/printer/print', type='json', auth='user', methods=['POST'])
    def print_receipt(self):
        """
        Receives base64 image from POS JS and prints it on the ESC/POS printer.
        """
        data = request.get_json_data()
        img_b64 = data.get('img')
        ip      = (data.get('ip') or '').strip()
        port    = int(data.get('port') or 9100)

        if not ip:
            return {'success': False, 'error': 'Printer IP is not configured.'}

        if not HAS_ESCPOS:
            return {
                'success': False,
                'error'  : 'python-escpos or Pillow not installed. '
                           'Run: pip install python-escpos Pillow',
            }

        try:
            img    = Image.open(io.BytesIO(base64.b64decode(img_b64)))
            slices = self._slice_image(img)

            printer = EscposNetwork(ip, port=port, profile='TM-T88IV')
            for sl in slices:
                printer.image(sl)
            printer.cut()
            time.sleep(1)
            printer.close()

            return {'success': True}

        except Exception as e:
            _logger.error('ia_pos_local: print error — %s', e)
            return {'success': False, 'error': str(e)}

    @http.route('/ia_pos_local/printer/test', type='json', auth='user', methods=['POST'])
    def test_connection(self):
        """Quick TCP ping to verify printer is reachable."""
        data = request.get_json_data()
        ip   = (data.get('ip') or '').strip()
        port = int(data.get('port') or 9100)
        try:
            sock = socket.create_connection((ip, port), timeout=5)
            sock.close()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _slice_image(img):
        """
        Splits a tall image into smaller chunks to avoid printer memory overflow.
        """
        w, h      = img.size
        slice_h   = max(20, h // 20)
        num       = (h + slice_h - 1) // slice_h
        slices    = []
        for i in range(num):
            y1 = i * slice_h
            y2 = min(h, (i + 1) * slice_h)
            slices.append(img.crop((0, y1, w, y2)))
        return slices
