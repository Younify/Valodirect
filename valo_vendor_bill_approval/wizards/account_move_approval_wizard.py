from odoo import models, fields, api


class AccountMoveApprovalWizard(models.TransientModel):
    _name = 'account.move.approval.wizard'
    _description = 'Account Move Approval Wizard'

    move_id = fields.Many2one('account.move', required=True, readonly=True)
    parnter_id = fields.Many2one('res.partner', related='move_id.partner_id')
    user_id = fields.Many2one('res.users', required=True, readonly=True)

    message = fields.Html('Comment')
    line_ids = fields.One2many(comodel_name='account.move.approval.wizard.line', inverse_name='wizard_id')

    def create(self, values):
        res = super().create(values)
        for wizard in res:
            wizard._compute_account_move_line_ids()
        return res

    def _compute_account_move_line_ids(self):
        self.ensure_one()

        my_lines = self.move_id.invoice_line_ids.filtered(lambda l: self.user_id.id in l.approver_user_id.ids)

        if self.env.user.has_group('valo_vendor_bill_approval.group_account_approver'):
            lines = self.move_id.invoice_line_ids
        else:
            lines = my_lines

        self.line_ids.unlink()
        for line in lines:
            vals = {
                'wizard_id': self.id,
                'move_line_id': line.id,
                'include_in_approval_selection': True if my_lines.filtered(lambda l: l.id == line.id) else False
            }
            self.env['account.move.approval.wizard.line'].sudo().create(vals)

    def approve(self):
        self._approve_lines(True)

    def decline(self):
        self._approve_lines(False)

    def _approve_lines(self, result):
        if self.message:
            self.move_id.message_post(body=self.message)

        selected_lines = self.line_ids.filtered(lambda l: l.include_in_approval_selection == True)
        self.move_id.approve_lines(result, selected_lines.move_line_id)


class AccountMoveApprovalWizardLine(models.TransientModel):
    _name = 'account.move.approval.wizard.line'

    wizard_id = fields.Many2one('account.move.approval.wizard')
    move_line_id = fields.Many2one('account.move.line')
    include_in_approval_selection = fields.Boolean('Inlcude')

    product_id = fields.Many2one(comodel_name='product.product', related='move_line_id.product_id')
    name = fields.Char(related='move_line_id.name')
    quantity = fields.Float(related='move_line_id.quantity')
    product_uom_id = fields.Many2one(comodel_name='uom.uom', related='move_line_id.product_uom_id')
    release_to_pay_qty_status = fields.Selection(related='move_line_id.release_to_pay_qty_status')
    price_unit = fields.Float(related='move_line_id.price_unit')
    release_to_pay_unit_price_status = fields.Selection(related='move_line_id.release_to_pay_unit_price_status')
    price_subtotal = fields.Monetary(related='move_line_id.price_subtotal')
    price_total = fields.Monetary(related='move_line_id.price_total')
    approver_user_id = fields.Many2many(comodel_name='res.users', related='move_line_id.approver_user_id')
    currency_id = fields.Many2one(comodel_name='res.currency', related='move_line_id.currency_id')
