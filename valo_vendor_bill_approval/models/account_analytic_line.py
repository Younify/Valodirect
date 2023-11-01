from odoo import models,api,fields

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    move_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Move Status',
        compute='_compute_move_status', store=True,
        readonly=True)
    
    payment_state = fields.Selection(
        selection=[
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
            ('reversed', 'Reversed'),
            ('invoicing_legacy', 'Invoicing App Legacy'),
        ],
        string="Move Payment Status", 
        compute='_compute_move_status', store=True,
        readonly=True)
    
    approval_status = fields.Selection(selection=[
            ('no', 'No'),
            ('yes', 'Yes'),
            ('waiting', 'Waiting'),
        ],
        string="Approval Status", 
        compute='_compute_move_status', store=True,
        readonly=True)
    
    @api.depends('move_line_id.approval_status','move_line_id.move_id.payment_state','move_line_id.move_id.state')
    def _compute_move_status(self):
        for line in self:
            line.move_state = False
            line.payment_state = False
            line.approval_status = False
            if line.move_line_id:
                line.move_state = line.move_line_id.move_id.state
                line.payment_state = line.move_line_id.move_id.payment_state
                line.approval_status = line.move_line_id.approval_status