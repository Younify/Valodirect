from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    def message_post(self, **kwargs):
        email_from_ctx = self.env.context.get('account_followup_email_from')
        default_email_from = kwargs.get('email_from')
        if email_from_ctx and not default_email_from:
            kwargs['email_from'] = email_from_ctx
        return super().message_post(**kwargs)
        
    