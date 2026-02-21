# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.translate import _


class HelpdeskSLA(models.Model):
    _name = 'helpdesk.sla'
    _description = 'Helpdesk SLA Policy'
    _order = 'priority desc, sequence, id'

    name = fields.Char('SLA Policy Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    description = fields.Text('Description', translate=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    team_id = fields.Many2one(
        'helpdesk.team', string='Helpdesk Team',
        required=True, ondelete='cascade',
    )
    stage_id = fields.Many2one(
        'helpdesk.stage', string='Target Stage',
        required=True,
        help="The stage the ticket must reach within the SLA deadline.",
    )
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Minimum Priority', default='0',
        help="SLA applies only to tickets with this priority or higher.",
    )
    category_ids = fields.Many2many(
        'helpdesk.category',
        'helpdesk_sla_category_rel',
        'sla_id', 'category_id',
        string='Categories',
        help="If set, SLA applies only to tickets in these categories. Leave empty for all.",
    )

    # Time limits
    time_days = fields.Integer('Days', default=0)
    time_hours = fields.Float('Hours', default=0)
    exclude_weekends = fields.Boolean(
        'Exclude Weekends',
        default=True,
        help="Do not count weekends in SLA deadline calculation.",
    )

    @api.depends('time_days', 'time_hours')
    def _compute_display_name(self):
        for sla in self:
            time_parts = []
            if sla.time_days:
                time_parts.append(_('%s day(s)', sla.time_days))
            if sla.time_hours:
                time_parts.append(_('%s hour(s)', sla.time_hours))
            time_str = ' '.join(time_parts) if time_parts else _('No limit')
            sla.display_name = f"{sla.name} ({time_str})"

    def _compute_sla_deadline(self, create_date):
        """Compute the SLA deadline from a given create_date."""
        self.ensure_one()
        from datetime import timedelta
        deadline = create_date + timedelta(days=self.time_days, hours=self.time_hours)
        if self.exclude_weekends:
            # Shift deadline forward for weekends
            days_added = 0
            current = create_date
            total_days = self.time_days
            while days_added < total_days:
                current += timedelta(days=1)
                if current.weekday() < 5:  # Mon-Fri
                    days_added += 1
            deadline = current + timedelta(hours=self.time_hours)
        return deadline
