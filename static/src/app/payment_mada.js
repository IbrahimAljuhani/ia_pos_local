/** @odoo-module */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";

/**
 * PaymentMada (Local)
 * -------------------
 * Handles Mada payment by calling the Odoo server controller,
 * which then connects to NeoLeap WebSocket directly.
 *
 * Flow:
 *   POS JS  →  POST /ia_pos_local/mada/pay
 *           →  Odoo Server → ws://IP:7000
 *           →  CHECK_STATUS → SALE
 *           →  result JSON → POS JS
 */
export class PaymentMadaLocal extends PaymentInterface {

    setup(pos, payment_method) {
        super.setup(...arguments);
        this.dialog = this.env.services.dialog;
        this.orm    = this.env.services.orm;
    }

    // ── Overrides ────────────────────────────────────────────────────────────

    send_payment_request(uuid) {
        super.send_payment_request(uuid);
        return this._madaPay(uuid);
    }

    send_payment_cancel(order, uuid) {
        super.send_payment_cancel(order, uuid);
        return this._madaCancel(uuid);
    }

    close() {}

    // ── Language helper ──────────────────────────────────────────────────────

    _t(ar, en) {
        const lang = this.env.services.user?.lang || 'en_US';
        return lang.startsWith('ar') ? ar : en;
    }

    _title() {
        return this._t('جهاز مدى', 'Mada Terminal');
    }

    // ── Payment flow ─────────────────────────────────────────────────────────

    async _madaPay(uuid) {
        const order = this.pos.get_order();
        const line  = order.payment_ids.find((l) => l.uuid === uuid);
        if (!line) return false;

        const neoleapIp = this.payment_method.neoleap_ip || '';
        if (!neoleapIp) {
            this._showError(
                this._t(
                    'لم يتم تكوين IP جهاز مدى. يرجى إدخاله في إعدادات طريقة الدفع.',
                    'NeoLeap IP address is not configured. Please set it in the payment method settings.'
                )
            );
            line.set_payment_status('retry');
            return false;
        }

        line.set_payment_status('waitingCard');

        try {
            const result = await this.env.services.rpc(
                '/ia_pos_local/mada/pay',
                {
                    neoleap_ip: neoleapIp,
                    amount    : line.amount.toFixed(2),
                    order_id  : order.uid || '',
                },
                { timeout: 100000 }
            );
            return this._handleResult(line, result);
        } catch (error) {
            this._showError(
                this._t(
                    'تعذّر الاتصال بالسيرفر. تحقق من الاتصال وحاول مجدداً.',
                    'Could not reach the server. Check your connection and try again.'
                )
            );
            line.set_payment_status('retry');
            return false;
        }
    }

    _handleResult(line, result) {
        if (!result) {
            this._showError(this._t('لم يصل رد من جهاز مدى.', 'No response from Mada terminal.'));
            line.set_payment_status('retry');
            return false;
        }

        if (result.success) {
            if (result.transactionId) line.transaction_id = result.transactionId;
            if (result.authCode)      line.card_type      = result.authCode;
            return true;
        }

        if (result.cancelled) {
            line.set_payment_status('retry');
            return false;
        }

        if (result.statusCode === '01') {
            this._showError(this._t('رفضت البنك البطاقة.', 'Transaction declined by the bank.'));
            line.set_payment_status('retry');
            return false;
        }

        const msg = result.errorMsg || this._t(
            'فشلت عملية الدفع. يرجى المحاولة مرة أخرى.',
            'Payment failed. Please try again.'
        );
        this._showError(msg);
        line.set_payment_status('retry');
        return false;
    }

    async _madaCancel(uuid) {
        const neoleapIp = this.payment_method.neoleap_ip || '';
        if (!neoleapIp) return true;
        try {
            await this.env.services.rpc('/ia_pos_local/mada/cancel', { neoleap_ip: neoleapIp });
        } catch {}
        return true;
    }

    // ── Manual payment fallback ──────────────────────────────────────────────

    async manualPayment(uuid) {
        const order = this.pos.get_order();
        const line  = order.payment_ids.find((l) => l.uuid === uuid);
        if (!line) return;

        const { confirmed, inputValue } = await new Promise((resolve) => {
            this.dialog.add(TextInputPopup, {
                title      : this._t('أدخل رقم الموافقة', 'Enter Approval Code'),
                placeholder: this._t('6 أحرف على الأقل', 'Minimum 6 characters'),
                getPayload : (val) => resolve({ confirmed: true,  inputValue: val }),
                close      : ()   => resolve({ confirmed: false, inputValue: '' }),
            });
        });

        if (!confirmed || !inputValue || inputValue.trim().length < 6) {
            if (confirmed) {
                this._showError(this._t(
                    'يجب أن يكون رقم الموافقة 6 أحرف على الأقل.',
                    'Approval code must be at least 6 characters.'
                ));
            }
            return;
        }

        line.transaction_id = inputValue.trim();
        line.set_payment_status('force_done');
    }

    // ── UI ───────────────────────────────────────────────────────────────────

    _showError(msg) {
        this.dialog.add(AlertDialog, { title: this._title(), body: msg });
    }
}
