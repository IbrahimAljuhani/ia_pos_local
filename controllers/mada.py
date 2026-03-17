# -*- coding: utf-8 -*-
"""
Mada payment controller.
Odoo server connects to NeoLeap WebSocket on behalf of the POS browser.
This avoids any Mixed Content issues even when Odoo runs on https://.
"""
import json
import logging
import threading

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

NEOLEAP_PORT    = 7000
STATUS_APPROVED  = '00'
STATUS_DECLINED  = '01'
STATUS_CANCELLED = '11'

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False
    _logger.warning(
        'ia_pos_local: websocket-client not installed. '
        'Run: pip install websocket-client'
    )


class MadaController(http.Controller):

    @http.route('/ia_pos_local/mada/pay', type='json', auth='user', methods=['POST'])
    def pay(self):
        """
        Receives payment request from POS JS.
        Connects to NeoLeap WebSocket, performs CHECK_STATUS → SALE,
        and returns result to POS.
        """
        data      = request.get_json_data()
        ip        = (data.get('neoleap_ip') or '').strip()
        amount    = str(data.get('amount', '0.00'))
        order_id  = str(data.get('order_id', ''))

        if not ip:
            return {'success': False, 'errorMsg': 'NeoLeap IP address is not configured.'}

        if not HAS_WEBSOCKET:
            return {
                'success' : False,
                'errorMsg': 'websocket-client is not installed on the server. '
                            'Run: pip install websocket-client',
            }

        return self._send_payment(ip, amount, order_id)

    @http.route('/ia_pos_local/mada/cancel', type='json', auth='user', methods=['POST'])
    def cancel(self):
        """Sends cancel command to NeoLeap."""
        data = request.get_json_data()
        ip   = (data.get('neoleap_ip') or '').strip()
        if not ip or not HAS_WEBSOCKET:
            return {'success': False}
        try:
            ws = websocket.create_connection('ws://%s:%d' % (ip, NEOLEAP_PORT), timeout=10)
            ws.send(json.dumps({'Command': 'CANCEL'}))
            ws.close()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'errorMsg': str(e)}

    # ── Internal ─────────────────────────────────────────────────────────────

    def _send_payment(self, ip, amount, order_id):
        url    = 'ws://%s:%d' % (ip, NEOLEAP_PORT)
        result = {'success': False, 'errorMsg': 'No response from Mada terminal.'}
        event  = threading.Event()

        def on_open(ws):
            _logger.info('MadaController: connected to %s — CHECK_STATUS', url)
            ws.send(json.dumps({'Command': 'CHECK_STATUS'}))

        def on_message(ws, message):
            nonlocal result
            try:
                data = json.loads(message)
            except Exception:
                result = {'success': False, 'errorMsg': 'Invalid response from terminal.'}
                ws.close(); event.set(); return

            event_name = data.get('EventName', '')

            if event_name == 'TERMINAL_STATUS':
                if data.get('TerminalStatus') == 'READY':
                    _logger.info('MadaController: READY — sending SALE amount=%s', amount)
                    ws.send(json.dumps({
                        'Command'       : 'SALE',
                        'Amount'        : amount,
                        'AdditionalData': order_id,
                    }))
                else:
                    result = {
                        'success' : False,
                        'errorMsg': 'Terminal is busy (%s). Please try again.' % data.get('TerminalStatus'),
                    }
                    ws.close(); event.set()

            elif event_name == 'TERMINAL_RESPONSE':
                result = self._parse_response(data)
                ws.close(); event.set()

        def on_error(ws, error):
            nonlocal result
            result = {'success': False, 'errorMsg': str(error)}
            event.set()

        def on_close(ws, *a):
            event.set()

        try:
            ws = websocket.WebSocketApp(
                url,
                on_open    = on_open,
                on_message = on_message,
                on_error   = on_error,
                on_close   = on_close,
            )
            t = threading.Thread(target=ws.run_forever)
            t.daemon = True
            t.start()
            if not event.wait(timeout=90):
                ws.close()
                result = {'success': False, 'errorMsg': 'Connection timed out (90 seconds).'}
        except Exception as e:
            result = {'success': False, 'errorMsg': str(e)}

        return result

    def _parse_response(self, data):
        jr          = data.get('JsonResult', {})
        status_code = jr.get('StatusCode', '')

        if status_code == STATUS_APPROVED:
            return {
                'success'      : True,
                'transactionId': jr.get('ECRReferenceNumber', ''),
                'authCode'     : jr.get('TransactionAuthCode', ''),
                'cardType'     : jr.get('CardType', ''),
                'statusCode'   : status_code,
            }
        elif status_code == STATUS_DECLINED:
            return {'success': False, 'errorMsg': 'Transaction declined by the bank.', 'statusCode': status_code}
        elif status_code == STATUS_CANCELLED:
            return {'success': False, 'cancelled': True, 'errorMsg': 'Transaction cancelled.', 'statusCode': status_code}
        else:
            return {'success': False, 'errorMsg': 'Unexpected response (StatusCode: %s).' % status_code, 'statusCode': status_code}
