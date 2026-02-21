# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.translate import _


class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'
    _inherit = ['mail.alias.mixin', 'mail.thread']
    _order = 'sequence, name'

    name = fields.Char('Team Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )
    description = fields.Html('Description', translate=True)
    color = fields.Integer('Color Index')

    # Members
    member_ids = fields.Many2many(
        'res.users', 'helpdesk_team_member_rel',
        'team_id', 'user_id', string='Team Members',
        domain=[('share', '=', False)],
    )
    leader_id = fields.Many2one(
        'res.users', string='Team Leader',
        domain=[('share', '=', False)],
    )

    # Stages
    stage_ids = fields.Many2many(
        'helpdesk.stage',
        'helpdesk_stage_team_rel',
        'team_id', 'stage_id',
        string='Stages',
    )

    # Assignment
    assignment_method = fields.Selection([
        ('manual', 'Manual'),
        ('random', 'Random'),
        ('balanced', 'Load Balanced'),
    ], string='Assignment Method', default='manual',
        help="Manual: tickets are not auto-assigned.\n"
             "Random: tickets are randomly assigned to team members.\n"
             "Load Balanced: tickets are assigned to the member with the least open tickets.",
    )

    # Features
    use_sla = fields.Boolean('SLA Policies', default=True)
    use_rating = fields.Boolean('Customer Ratings', default=True)
    use_timesheet = fields.Boolean('Time Tracking')

    # Stats
    ticket_count = fields.Integer('Open Tickets', compute='_compute_ticket_stats')
    ticket_closed_count = fields.Integer('Closed Tickets', compute='_compute_ticket_stats')
    ticket_unassigned_count = fields.Integer('Unassigned Tickets', compute='_compute_ticket_stats')
    sla_failed_count = fields.Integer('SLA Failed', compute='_compute_ticket_stats')
    avg_rating = fields.Float('Average Rating', compute='_compute_ticket_stats')

    @api.depends_context('uid')
    def _compute_ticket_stats(self):
        for team in self:
            domain = [('team_id', '=', team.id)]
            tickets = self.env['helpdesk.ticket'].search(domain)
            open_tickets = tickets.filtered(lambda t: not t.stage_id.is_close)
            closed_tickets = tickets.filtered(lambda t: t.stage_id.is_close)
            team.ticket_count = len(open_tickets)
            team.ticket_closed_count = len(closed_tickets)
            team.ticket_unassigned_count = len(open_tickets.filtered(lambda t: not t.user_id))
            team.sla_failed_count = len(open_tickets.filtered(lambda t: t.sla_deadline and t.sla_deadline < fields.Datetime.now()))
            ratings = closed_tickets.mapped('rating_last_value')
            team.avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

    # --- Mail Alias ---
    def _alias_get_creation_values(self):
        values = super()._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('helpdesk.ticket').id
        if self.id:
            values['alias_defaults'] = {'team_id': self.id}
        return values

    # --- Auto Assignment ---
    def _auto_assign_ticket(self, ticket):
        """Auto-assign a ticket based on the team's assignment method."""
        self.ensure_one()
        if self.assignment_method == 'manual' or not self.member_ids:
            return
        if self.assignment_method == 'random':
            import random
            ticket.user_id = random.choice(self.member_ids)
        elif self.assignment_method == 'balanced':
            # Assign to member with least open tickets
            member_ticket_count = {}
            open_tickets = self.env['helpdesk.ticket'].search([
                ('team_id', '=', self.id),
                ('stage_id.is_close', '=', False),
                ('user_id', 'in', self.member_ids.ids),
            ])
            for member in self.member_ids:
                member_ticket_count[member.id] = len(open_tickets.filtered(lambda t: t.user_id == member))
            least_loaded = min(member_ticket_count, key=member_ticket_count.get)
            ticket.user_id = least_loaded

    def action_view_tickets(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('helpdesk_mgmt.helpdesk_ticket_action')
        action['domain'] = [('team_id', '=', self.id)]
        action['context'] = {'default_team_id': self.id}
        return action
