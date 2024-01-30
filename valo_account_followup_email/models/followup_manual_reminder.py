from odoo import _, api, fields, models


class FollowupManualReminder(models.TransientModel):
    _inherit = 'account_followup.manual_reminder'
    
    def _get_wizard_options(self):
        res = super()._get_wizard_options()
        if self.template_id.email_from:
            ctx = dict.copy(self.env.context)
            ctx['account_followup_email_from'] = self.template_id.email_from
            self.env.context = ctx
            
        return res
