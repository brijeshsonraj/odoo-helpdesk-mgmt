# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HelpdeskStage(models.Model):
    _name = 'helpdesk.stage'
    _description = 'Helpdesk Ticket Stage'
    _order = 'sequence, id'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    fold = fields.Boolean(
        'Folded in Kanban',
        help="This stage is folded in the kanban view when there are no records in that stage to display.",
    )
    is_close = fields.Boolean(
        'Closing Stage',
        help="Tickets in this stage are considered as closed/done.",
    )
    team_ids = fields.Many2many(
        'helpdesk.team',
        'helpdesk_stage_team_rel',
        'stage_id', 'team_id',
        string='Teams',
        help="Teams that use this stage. If empty, the stage is available for all teams.",
    )
    template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'helpdesk.ticket')]",
        help="Automated email sent to the customer when the ticket reaches this stage.",
    )
    description = fields.Text('Description', translate=True)

    def _get_default_team_ids(self):
        team_id = self.env.context.get('default_team_id')
        if team_id:
            return [(4, team_id)]
        return []
