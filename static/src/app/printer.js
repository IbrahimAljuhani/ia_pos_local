/** @odoo-module */

import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * EscPosLocalPrinter
 * ------------------
 * Sends receipt/kitchen images to the Odoo server controller,
 * which then forwards them to the ESC/POS printer over TCP.
 */
export class EscPosLocalPrinter extends BasePrinter {

    setup({ ip, port }) {
        super.setup(...arguments);
        this.url  = '/ia_pos_local/printer/print';
        this.ip   = ip;
        this.port = port || 9100;
    }

    openCashbox() {
        // Cash drawer open via printer pulse — can be extended if needed
    }

    async sendPrintingJob(img) {
        try {
            const res = await fetch(this.url, {
                method : 'POST',
                headers: {
                    'Accept'      : 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    img : img,
                    ip  : this.ip,
                    port: this.port,
                }),
            });
            const body = await res.json();
            if (body.result && body.result.success === false) {
                console.error('ia_pos_local: print error —', body.result.error);
            }
        } catch (e) {
            console.error('ia_pos_local: printer request failed —', e);
        }
        return { result: true, printerErrorCode: 0 };
    }
}

// ── Register printer in PosStore ─────────────────────────────────────────────

patch(PosStore.prototype, {
    create_printer(config) {
        if (config.printer_type === 'escpos_local') {
            return new EscPosLocalPrinter({
                ip  : config.escpos_local_ip,
                port: config.escpos_local_port || 9100,
            });
        }
        return super.create_printer(...arguments);
    },
});
