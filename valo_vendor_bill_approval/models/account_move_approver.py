from odoo import models,fields,api
from odoo.exceptions import UserError

class AccountMoveApprover(models.Model):
    _name = 'account.move.approver'
    _description = 'Account Move Approver'

    release_to_pay_status = fields.Selection([
        ('waiting','Waiting'),
        ('yes','Yes'),
        ('no','No')
    ],'Should be paid', readonly=True)

    override = fields.Boolean('Accountant Approval', readonly=True)
    approval_date = fields.Datetime('Approval Date', readonly=True)
    user_id = fields.Many2one('res.users', readonly=True)
    all_lines_reviewed = fields.Boolean('All Lines Reviewed', compute= '_compute_all_lines_reviewed')

    move_id = fields.Many2one('account.move')

    @api.constrains('user_id')
    def _check_constraint_same_user_id(self):
        for line in self:
            candidates = self.search([('move_id','=', line.move_id.id),('user_id','=', line.user_id.id),('id','!=', line.id)])
            if len(candidates) > 0:
                raise UserError('This user is already in the approval list')


    def _compute_all_lines_reviewed(self):
        for approver in self:
            my_waiting_lines = approver.move_id.invoice_line_ids.filtered(lambda l: approver.user_id.id in l.approver_user_id.ids)
            my_waiting_lines = my_waiting_lines.filtered(lambda l: l.release_to_pay_unit_price_status == 'waiting' or l.release_to_pay_qty_status == 'waiting')
            approver.sudo().all_lines_reviewed = False if my_waiting_lines else True