from odoo import models,fields,api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Product Template'

    analytic_account_id = fields.Many2one('account.analytic.account')
    