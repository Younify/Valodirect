from odoo import models,api,fields
from odoo.osv.expression import AND

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    approver_ids = fields.Many2many('res.users',compute='_compute_approvers_user_ids',store=True)

    @api.depends('move_line_id.approver_user_id')
    def _compute_approvers_user_ids(self):
        for line in self:
            line.approver_ids = line.move_line_id.approver_user_id.ids

#For some reason the access rights where not working so we add it here
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('valo_vendor_bill_approval_approver_only.group_account_analytic_line_approver_only'):
            domain = AND([domain, self._get_approver_domain()])
        return super(AccountAnalyticLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy) 
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('valo_vendor_bill_approval_approver_only.group_account_analytic_line_approver_only'):
            if not args:
                args = self._get_approver_domain()
            else:
                args = AND([args,self._get_approver_domain()])
        return super(AccountAnalyticLine, self).search(args, offset=offset, limit=limit, order=order, count=count)  
        
    @api.model
    def _get_approver_domain(self):
        return ['|', ('approver_ids', '=', False), ('approver_ids', 'in', self.env.user.id)]