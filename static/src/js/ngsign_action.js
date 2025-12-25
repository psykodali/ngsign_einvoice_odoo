/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { BlockUI } from "@web/core/ui/block_ui";

async function actionSignNGSignJs(env, action) {
    const rpc = env.services.rpc;
    const ui = env.services.ui;
    const notification = env.services.notification;

    const activeIds = action.params.active_ids;

    if (!activeIds || activeIds.length === 0) {
        notification.add(_t("No invoices selected."), { type: "warning" });
        return;
    }

    // Block UI with first message
    ui.block({ message: _t("1- Preparing eInvoices") });

    try {
        // Step 1: Prepare (Generate PDFs)
        await rpc("/web/dataset/call_kw/account.move/action_ngsign_prepare", {
            model: "account.move",
            method: "action_ngsign_prepare",
            args: [activeIds],
            kwargs: {},
        });

        // Step 2: Send (Update message and call API)
        // Note: ui.block replaces the message if called again? 
        // In Odoo 16+ usually we unblock and block again or just update. 
        // Let's try unblocking and blocking to be safe and ensure message update.
        ui.unblock();
        ui.block({ message: _t("2- Sending eInvoices for signature") });

        const result = await rpc("/web/dataset/call_kw/account.move/action_ngsign_send", {
            model: "account.move",
            method: "action_ngsign_send",
            args: [activeIds],
            kwargs: {},
        });

        // Show success notification if needed, or let the backend action handle it (e.g. reload)
        notification.add(_t("Process completed successfully."), { type: "success" });

        // Return an action to reload the view or similar
        return { type: "ir.actions.client", tag: "reload" };

    } catch (error) {
        console.error("NGSign Error:", error);
        // Error handling is usually done by RPC service, but we can add custom notification
        // notification.add(_t("An error occurred during signing."), { type: "danger" });
        // Re-throw to let Odoo handle the error dialog
        throw error;
    } finally {
        ui.unblock();
    }
}

registry.category("actions").add("ngsign_einvoice_odoo.action_sign_ngsign_js", actionSignNGSignJs);
