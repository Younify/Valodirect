# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vendor_bill_unit_price_margin = fields.Float('Vendor Bill Unit Price Margin [%]', config_parameter='account.vendor_bill_unit_price_margin')
    vendor_bill_total_untaxed_margin = fields.Float('Vendor Bill Total Untaxed Margin', config_parameter='account.vendor_bill_total_untaxed_margin')