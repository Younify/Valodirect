from odoo import models,fields,api
from datetime import datetime

from odoo.tools.float_utils import float_compare, float_round

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    release_to_pay_unit_price_status = fields.Selection([
        ('waiting','Waiting Approval'),
        ('yes','Yes'),
        ('no','No')
    ],'Release Pay Unit Status', readonly=True)

    release_to_pay_qty_status = fields.Selection([
        ('waiting','Waiting Approval'),
        ('yes','Yes'),
        ('no','No')
    ],'Release Pay Qty Status', readonly=True)

    approver_user_id = fields.Many2many('res.users','account_move_line_approver_rel',readonly=True,compute='update_approval_list', store=True)
    manual_approver_user_id = fields.Many2many('res.users','account_move_line_manual_approver_rel')

    approved_by_user_id = fields.Many2one('res.users', readonly=True)
    approval_date = fields.Datetime('Approval date', readonly=True)

    @api.depends('analytic_line_ids')
    def update_approval_list(self):
        for line in self:

            if not type(line.id) == int:
                continue

            approvers = line.manual_approver_user_id
            managers = None
            #search related project
            analytic_ids = []

            if line.analytic_distribution:
                line_analytic_keys = line.analytic_distribution.keys()
                line_analytic_ids = []
                for key in line_analytic_keys:
                    line_analytic_ids.append(int(key))
                
                analytic_ids += line_analytic_ids
            

            po_line = line.purchase_line_id
            if po_line.analytic_distribution:
                po_analytic_keys = po_line.analytic_distribution.keys()
                po_analytic_ids = []
                for key in po_analytic_keys:
                    po_analytic_ids.append(int(key))

                analytic_ids += po_analytic_ids

            if analytic_ids:
                projects = self.env['project.project'].search([('analytic_account_id','in', analytic_ids)])
                managers = projects.user_id 

            #if we can't find it here maybe there is a po linked
      

            #if no approver but line has already approver its added manual so don't touch
            if managers:
                approvers |= managers
            else:
                default_approvers = self.env['res.groups'].sudo().search([('name','=','Vendor Bill Approver (No Project)')]).users
                if default_approvers:
                    approvers |= default_approvers

            line.approver_user_id = [fields.Command.set(approvers.ids)]

        #upddate approval list
        self.move_id.update_approval_line_id()

    def approve_line(self):
        for line in self:
            line.approval_date = datetime.now()
            line.release_to_pay_unit_price_status = 'yes'
            line.release_to_pay_qty_status = 'yes'
            line.approved_by_user_id = self.env.user.id

    def decline_line(self):
        for line in self:
            line.approval_date = datetime.now()
            line.release_to_pay_unit_price_status = 'no'
            line.release_to_pay_qty_status = 'no'
            line.approved_by_user_id = self.env.user.id

    def _can_be_paid(self):

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoice_line_tolerance = self.env['ir.config_parameter'].sudo().get_param('account.vendor_bill_unit_price_margin')

        if not invoice_line_tolerance:
            invoice_line_tolerance = 100

        for invoice_line in self:
            po_line = invoice_line.purchase_line_id

            #set default values
            if invoice_line.release_to_pay_unit_price_status not in ('yes','no'):
                invoice_line.release_to_pay_unit_price_status = 'waiting'

            if invoice_line.release_to_pay_qty_status not in ('yes','no'):
                invoice_line.release_to_pay_qty_status = 'waiting'

            unit_price_ok = False
            qty_ok = False

            #No po line line will need approval
            if not po_line:
                continue

            invoiced_qty = po_line.qty_invoiced
            received_qty = po_line.qty_received
            ordered_qty = po_line.product_qty

            # A price difference between the original order and the invoice results in an exception
            invoice_currency = invoice_line.currency_id
            order_currency = po_line.currency_id
            invoice_converted_price = invoice_currency._convert(
                    invoice_line.price_unit, order_currency, invoice_line.company_id, fields.Date.today())
            
            #Check for the price
            unit_price_po = float_round(value=po_line.price_unit, precision_rounding=order_currency.rounding)
            unit_price_bill = float_round(value=invoice_converted_price, precision_rounding=order_currency.rounding)

            #Check unit price bill in tolerance
            difference = unit_price_bill - unit_price_po
            if unit_price_po != 0:
                margin = (difference / unit_price_po) * 100
                margin = abs(margin)

                if margin <= invoice_line_tolerance:
                    unit_price_ok = True
            
            #Check for qty
            if po_line.product_id.purchase_method == 'purchase': # 'on ordered quantities'
                if float_compare(invoiced_qty, ordered_qty, precision_digits=precision) <= 0:
                    qty_ok = True
            else:
                if float_compare(invoiced_qty, received_qty, precision_digits=precision) <= 0:
                    qty_ok = True

            if unit_price_ok:
                invoice_line.release_to_pay_unit_price_status = 'yes'

            if qty_ok:
                invoice_line.release_to_pay_qty_status = 'yes'