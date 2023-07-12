from odoo import models,fields
from odoo.exceptions import UserError
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    

    def _create_invoices(self, grouped=False, final=False, date=None):
        if grouped:
            raise UserError('Grouping sale orders is not allowed')
        moves = super()._create_invoices(grouped,final,date)
        for line in moves.invoice_line_ids:
            sales = line.sale_line_ids
            if sales:
                if len(sales) > 1:
                    raise UserError('An invoice line can only be related to one analytic line')
                line.analytic_distribution  =  sales.analytic_distribution 

        return moves
                
    