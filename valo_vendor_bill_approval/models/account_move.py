from odoo import _, api, fields, models
from odoo.exceptions import UserError

from datetime import datetime

class accountSecurity(models.Model):
    _inherit = 'account.move'
    
    approval_line_id = fields.One2many(comodel_name='account.move.approver',inverse_name='move_id')
    pending_approvers = fields.Many2many(comodel_name='res.users',relation='account_move_approver_rel',string='Pending Approvers',store=True,compute='_compute_pending_approvers')
    release_to_pay = fields.Selection(selection_add=[
        ('waiting', 'Waiting')
        ])

    @api.depends('invoice_line_ids.release_to_pay_unit_price_status','invoice_line_ids.release_to_pay_qty_status','invoice_line_ids.approver_user_id','invoice_line_ids.approval_date')
    def _compute_pending_approvers(self):
        for move in self:
            users = self.env['res.users']
            waiting_lines = move.invoice_line_ids.filtered(lambda l: l.release_to_pay_unit_price_status == 'waiting' or l.release_to_pay_qty_status == 'waiting')
            users |= waiting_lines.approver_user_id
            move.pending_approvers = users

    def update_approval_line_id(self):
        for move in self:
            approvers = move.invoice_line_ids.approver_user_id

            for approver in approvers:
                candidate = self.approval_line_id.filtered(lambda a: a.user_id == approver)
                if not candidate:
                    self.env['account.move.approver'].sudo().create({
                        'move_id': move.id,
                        'user_id': approver.id,
                        'override': False,
                        'release_to_pay_status': 'waiting'
                    })

            #remove all lines that are no approver anymore
            approvers_unlink = self.approval_line_id.filtered(lambda a: a.user_id.id not in approvers.ids)
            self.env['account.move.approver'].sudo().browse(approvers_unlink.ids).sudo().unlink()

    def action_open_approve_lines_wizard(self):
        #this will return a wizard with the lines to approve and option to log a note
        self.ensure_one()

        

        wizard_id = self.env['account.move.approval.wizard'].create({
            'user_id':self.env.user.id,
            'move_id':self.id
        })

        if not len(wizard_id.line_ids):
            raise UserError('No accounting lines to approve')

        return {
            "name": 'Approve vendor Bill',
            "type": 'ir.actions.act_window',
            "res_model": 'account.move.approval.wizard',
            "view_mode": 'form',
            "view_type": 'form',
            "res_id": wizard_id.id,
            "target": "new",
        }

    def approve_lines(self,approved,lines):
        self.ensure_one()
        #get all lines that are for the user
        user = self.env.user
        if approved:
            lines.approve_line()
        else:
             lines.decline_line()

        #update the approvers list status
        approval_line = self.approval_line_id.filtered(lambda a: a.user_id.id == user.id)
        if approval_line:
            approval_line.sudo().approval_date = datetime.now()
            approval_line.sudo().release_to_pay_status = 'yes' if approved else 'no'

        #if the user is admin approver we mark override
        if self.env.user.has_group('valo_vendor_bill_approval.group_account_approver'):

            approver_ids = lines.approver_user_id.ids
            move_approvers = self.approval_line_id.filtered(lambda l: l.user_id.id in approver_ids)
            move_approvers.override = True

        #log a note that its has been approved or not
        if approved:
            self.message_post(body='Document approved')
        else:
            self.message_post(body='Document declined')
    
    @api.depends('invoice_line_ids.release_to_pay_unit_price_status','invoice_line_ids.release_to_pay_qty_status')
    def _compute_release_to_pay(self):
        records = self
        invoice_tolerance = self.env['ir.config_parameter'].sudo().get_param('account.vendor_bill_total_untaxed_margin')

        if not invoice_tolerance:
            invoice_tolerance = 0
        else:
            invoice_tolerance = float(invoice_tolerance)

        if self.env.context.get('module') == 'account_3way_match':
            # on module installation we set 'no' for all paid bills and other non relevant records at once
            records = records.filtered(lambda r: r.payment_state != 'paid' and r.move_type in ('in_invoice', 'in_refund'))
            (self - records).release_to_pay = 'no'

        for invoice in records:
            if invoice.payment_state == 'paid' or not invoice.is_invoice(include_receipts=True):
                # no need to pay, if it's already paid
                invoice.release_to_pay = 'no'

            #Check if all the lines are yes
            yes_line = invoice.invoice_line_ids.filtered(lambda l: l.release_to_pay_unit_price_status == 'yes' and l.release_to_pay_qty_status == 'yes')
            if len(yes_line) == len(invoice.invoice_line_ids):
                invoice.release_to_pay = 'yes'
                continue

            #Check if there is one line with payment status no
            no_line = invoice.invoice_line_ids.filtered(lambda l: l.release_to_pay_unit_price_status == 'no' or l.release_to_pay_qty_status == 'no')
            if no_line:
                invoice.release_to_pay = 'no'
                continue

            #Check if there is one line with waiting status
            waiting_line = invoice.invoice_line_ids.filtered(lambda l: l.release_to_pay_unit_price_status == 'waiting' or l.release_to_pay_qty_status == 'waiting')
            if waiting_line:
                invoice.release_to_pay = 'waiting'

            qty_nok_line = invoice.invoice_line_ids.filtered(lambda l: l.release_to_pay_qty_status != 'yes')
            if qty_nok_line:
                continue

            # if we get here this means all qty lines are yes
            # its possible that some unit price checks are no or waiting this can be overriden if the total price of the bill is in margin
            invoice_currency = invoice.currency_id

            total_price_untaxed_po = 0
            for po_line in invoice.invoice_line_ids.purchase_line_id:
                order_currency = po_line.currency_id
                converted_price = po_line.price_subtotal
                #We need to convert the pricing to compare
                converted_price = order_currency._convert(converted_price,invoice_currency,po_line.company_id, fields.Date.today())

                total_price_untaxed_po += converted_price

            total_price_untaxed_bill = invoice.amount_untaxed

            difference = total_price_untaxed_bill - total_price_untaxed_po
            if total_price_untaxed_po != 0:
                margin = difference
                margin = abs(margin)
                if  margin <= invoice_tolerance:
                    invoice.release_to_pay = 'yes'
                    #all invoice lines can also be put yes now because total is fine
                    invoice.invoice_line_ids.release_to_pay_unit_price_status ='yes'
                    continue
        
            invoice.release_to_pay = 'waiting'  

    def button_draft(self):
        res = super().button_draft()
        for move in self:
            for line in move.invoice_line_ids:
                line.release_to_pay_unit_price_status = 'waiting'
                line.release_to_pay_qty_status = 'waiting'
                line.approved_by_user_id = False
                line.approval_date = False
                line._can_be_paid()
            move._compute_release_to_pay()
        return res
    
    def action_restart_approval(self):
        for move in self:
            for line in move.invoice_line_ids:
                line.release_to_pay_unit_price_status = 'waiting'
                line.release_to_pay_qty_status = 'waiting'
                line.approved_by_user_id = False
                line.approval_date = False
                line._can_be_paid()
                line.update_approval_list()
            move._compute_release_to_pay()

            move.approval_line_id.release_to_pay_status = 'waiting'
            move.approval_line_id.override = False
            move.approval_line_id.approval_date = False

            move.message_post(body='Approval restarted')

    def action_post(self):
        res = super().action_post()
        self.action_restart_approval()
        return res