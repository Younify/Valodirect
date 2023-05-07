from odoo import models,fields,api

class AccountMoveApprovalWizard(models.TransientModel):
    _name = 'account.move.approval.wizard'
    _description = 'Account Move Approval Wizard'

    move_id = fields.Many2one('account.move',required=True, readonly=True)
    parnter_id = fields.Many2one('res.partner', related='move_id.partner_id')
    user_id = fields.Many2one('res.users', required=True, readonly=True)

    message = fields.Html('Comment')
    move_line_ids = fields.One2many(comodel_name='account.move.line', compute='_compute_account_move_line_ids', readonly=True)


    def _compute_account_move_line_ids(self):
        self.ensure_one()

        if self.env.user.has_group('valo_vendor_bill_approval.group_account_approver') :
            self.move_line_ids = self.move_id.invoice_line_ids
        else:
            lines = self.move_id.invoice_line_ids.filtered(lambda l: self.user_id.id in l.approver_user_id.ids)
            self.move_line_ids = lines


    def approve(self):
        if self.message:
            self.move_id.message_post(body=self.message)
        self.move_id.approve_lines(True,self.move_line_ids)

    def decline(self):
        if self.message:
            self.move_id.message_post(body=self.message)
        self.move_id.approve_lines(False,self.move_line_ids)

    