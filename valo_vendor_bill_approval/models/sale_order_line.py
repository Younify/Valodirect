from odoo import models,fields,api

class saleOrderLine(models.Model):
    _inherit = 'sale.order.line'  
    _description = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_product_id_analytic(self):
        for line in self:
            if line.product_id.analytic_account_id:
                line.analytic_distribution =  {line.product_id.analytic_account_id.id:100}
    