# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError


TICKET_PRIORITY = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Urgent'),
]


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = [
        'mail.thread.cc',
        'mail.activity.mixin',
        'portal.mixin',
        'rating.mixin',
        'utm.mixin',
    ]
    _order = 'priority desc, create_date desc, id desc'
    _mail_post_access = 'read'
    _primary_email = 'partner_email'

    # --- Core Fields ---
    name = fields.Char(
        'Subject', required=True, index='trigram',
        tracking=True,
    )
    number = fields.Char(
        'Ticket Number', readonly=True, copy=False,
        default=lambda self: _('New'),
    )
    description = fields.Html('Description', sanitize_style=True)
    active = fields.Boolean(default=True)

    # --- Relationships ---
    team_id = fields.Many2one(
        'helpdesk.team', string='Team',
        required=True, tracking=True,
        default=lambda self: self.env['helpdesk.team'].search([], limit=1),
    )
    stage_id = fields.Many2one(
        'helpdesk.stage', string='Stage',
        tracking=True, index=True,
        copy=False, group_expand='_read_group_stage_ids',
        domain="['|', ('team_ids', '=', False), ('team_ids', 'in', team_id)]",
    )
    user_id = fields.Many2one(
        'res.users', string='Assigned To',
        tracking=True, index=True,
        domain=[('share', '=', False)],
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        tracking=True, index=True,
    )
    partner_email = fields.Char(
        'Customer Email',
        compute='_compute_partner_email',
        inverse='_inverse_partner_email',
        store=True, readonly=False,
    )
    partner_phone = fields.Char(
        'Customer Phone',
        compute='_compute_partner_phone',
        inverse='_inverse_partner_phone',
        store=True, readonly=False,
    )
    category_id = fields.Many2one(
        'helpdesk.category', string='Category',
        tracking=True,
    )
    tag_ids = fields.Many2many(
        'helpdesk.tag', 'helpdesk_ticket_tag_rel',
        'ticket_id', 'tag_id', string='Tags',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='team_id.company_id', store=True, readonly=True,
    )

    # --- Priority & Status ---
    priority = fields.Selection(
        TICKET_PRIORITY, string='Priority',
        default='1', tracking=True,
    )
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked'),
    ], string='Kanban State', default='normal', tracking=True)
    is_closed = fields.Boolean(
        'Closed', related='stage_id.is_close',
        store=True, readonly=True,
    )
    color = fields.Integer('Color Index')

    # --- SLA ---
    sla_ids = fields.Many2many(
        'helpdesk.sla', 'helpdesk_ticket_sla_rel',
        'ticket_id', 'sla_id', string='SLA Policies',
        compute='_compute_sla_ids', store=True,
    )
    sla_deadline = fields.Datetime(
        'SLA Deadline', compute='_compute_sla_deadline',
        store=True, tracking=True,
    )
    sla_reached_datetime = fields.Datetime('SLA Reached Date', readonly=True)
    sla_status = fields.Selection([
        ('ongoing', 'Ongoing'),
        ('reached', 'Reached'),
        ('failed', 'Failed'),
    ], string='SLA Status', compute='_compute_sla_status', store=True)
    sla_status_color = fields.Integer(
        'SLA Color', compute='_compute_sla_status',
    )

    # --- Dates ---
    date_deadline = fields.Date('Deadline', tracking=True)
    date_first_response = fields.Datetime('First Response Date', readonly=True)
    date_closed = fields.Datetime('Closed Date', readonly=True)
    response_hours = fields.Float(
        'First Response Hours', compute='_compute_response_hours',
        store=True,
    )
    close_hours = fields.Float(
        'Hours to Close', compute='_compute_close_hours',
        store=True,
    )

    # --- Time Tracking ---
    timesheet_hours = fields.Float('Hours Spent', default=0.0)

    # --- Rating ---
    rating_last_value = fields.Float('Rating Value', default=0.0)

    # --- Counts ---
    attachment_count = fields.Integer(
        'Attachments', compute='_compute_attachment_count',
    )

    # --- Computed Display ---
    kanban_state_label = fields.Char(
        'Kanban State Label', compute='_compute_kanban_state_label',
    )

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id)',
         'Ticket number must be unique per company!'),
    ]

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('partner_id')
    def _compute_partner_email(self):
        for ticket in self:
            if ticket.partner_id and not ticket.partner_email:
                ticket.partner_email = ticket.partner_id.email

    def _inverse_partner_email(self):
        for ticket in self.filtered(lambda t: t.partner_email and not t.partner_id):
            partner = self.env['res.partner'].search(
                [('email', '=', ticket.partner_email)], limit=1,
            )
            if partner:
                ticket.partner_id = partner

    @api.depends('partner_id')
    def _compute_partner_phone(self):
        for ticket in self:
            if ticket.partner_id and not ticket.partner_phone:
                ticket.partner_phone = ticket.partner_id.phone

    def _inverse_partner_phone(self):
        pass

    @api.depends('team_id', 'priority', 'category_id')
    def _compute_sla_ids(self):
        for ticket in self:
            if not ticket.team_id:
                ticket.sla_ids = False
                continue
            domain = [
                ('team_id', '=', ticket.team_id.id),
                ('priority', '<=', ticket.priority),
            ]
            sla_policies = self.env['helpdesk.sla'].search(domain)
            # Filter by category if specified on the SLA
            applicable = sla_policies.filtered(
                lambda s: not s.category_ids or ticket.category_id in s.category_ids
            )
            ticket.sla_ids = applicable

    @api.depends('sla_ids', 'create_date')
    def _compute_sla_deadline(self):
        for ticket in self:
            if not ticket.sla_ids or not ticket.create_date:
                ticket.sla_deadline = False
                continue
            # Take the tightest (earliest) deadline
            deadlines = []
            for sla in ticket.sla_ids:
                dl = sla._compute_sla_deadline(ticket.create_date)
                deadlines.append(dl)
            ticket.sla_deadline = min(deadlines) if deadlines else False

    @api.depends('sla_deadline', 'is_closed', 'sla_reached_datetime')
    def _compute_sla_status(self):
        now = fields.Datetime.now()
        for ticket in self:
            if not ticket.sla_deadline:
                ticket.sla_status = False
                ticket.sla_status_color = 0
            elif ticket.sla_reached_datetime:
                if ticket.sla_reached_datetime <= ticket.sla_deadline:
                    ticket.sla_status = 'reached'
                    ticket.sla_status_color = 10  # green
                else:
                    ticket.sla_status = 'failed'
                    ticket.sla_status_color = 1  # red
            elif now > ticket.sla_deadline:
                ticket.sla_status = 'failed'
                ticket.sla_status_color = 1
            else:
                ticket.sla_status = 'ongoing'
                ticket.sla_status_color = 4  # blue

    @api.depends('create_date', 'date_first_response')
    def _compute_response_hours(self):
        for ticket in self:
            if ticket.create_date and ticket.date_first_response:
                delta = ticket.date_first_response - ticket.create_date
                ticket.response_hours = delta.total_seconds() / 3600.0
            else:
                ticket.response_hours = 0.0

    @api.depends('create_date', 'date_closed')
    def _compute_close_hours(self):
        for ticket in self:
            if ticket.create_date and ticket.date_closed:
                delta = ticket.date_closed - ticket.create_date
                ticket.close_hours = delta.total_seconds() / 3600.0
            else:
                ticket.close_hours = 0.0

    def _compute_attachment_count(self):
        attachment_data = self.env['ir.attachment']._read_group(
            [('res_model', '=', 'helpdesk.ticket'), ('res_id', 'in', self.ids)],
            ['res_id'],
            ['__count'],
        )
        mapped_data = {res_id: count for res_id, count in attachment_data}
        for ticket in self:
            ticket.attachment_count = mapped_data.get(ticket.id, 0)

    @api.depends('kanban_state')
    def _compute_kanban_state_label(self):
        labels = dict(self._fields['kanban_state'].selection)
        for ticket in self:
            ticket.kanban_state_label = labels.get(ticket.kanban_state, '')

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('New')) == _('New'):
                vals['number'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or _('New')
            # Set default stage
            if not vals.get('stage_id') and vals.get('team_id'):
                team = self.env['helpdesk.team'].browse(vals['team_id'])
                if team.stage_ids:
                    vals['stage_id'] = team.stage_ids[0].id

        tickets = super().create(vals_list)

        # Auto-assign tickets
        for ticket in tickets:
            if not ticket.user_id and ticket.team_id:
                ticket.team_id._auto_assign_ticket(ticket)

        return tickets

    def write(self, vals):
        # Track stage changes
        if 'stage_id' in vals:
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            now = fields.Datetime.now()
            if stage.is_close:
                vals['date_closed'] = now
                for ticket in self:
                    if not ticket.sla_reached_datetime:
                        vals['sla_reached_datetime'] = now
            else:
                vals['date_closed'] = False

        res = super().write(vals)

        # Send email template when stage changes
        if 'stage_id' in vals:
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if stage.template_id:
                for ticket in self:
                    stage.template_id.send_mail(ticket.id, force_send=False)

        return res

    def unlink(self):
        for ticket in self:
            if ticket.is_closed:
                raise UserError(_("You cannot delete a closed ticket. Archive it instead."))
        return super().unlink()

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------

    def action_close_ticket(self):
        """Move ticket to the first closing stage."""
        for ticket in self:
            close_stage = self.env['helpdesk.stage'].search([
                ('is_close', '=', True),
                '|', ('team_ids', '=', False), ('team_ids', 'in', ticket.team_id.id),
            ], limit=1)
            if close_stage:
                ticket.stage_id = close_stage

    def action_reopen_ticket(self):
        """Move ticket back to the first open stage."""
        for ticket in self:
            open_stage = self.env['helpdesk.stage'].search([
                ('is_close', '=', False),
                '|', ('team_ids', '=', False), ('team_ids', 'in', ticket.team_id.id),
            ], order='sequence', limit=1)
            if open_stage:
                ticket.stage_id = open_stage
                ticket.sla_reached_datetime = False

    def action_assign_to_me(self):
        self.write({'user_id': self.env.uid})

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('res_model', '=', 'helpdesk.ticket'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'helpdesk.ticket',
                'default_res_id': self.id,
            },
        }

    def action_open_rating(self):
        self.ensure_one()
        return {
            'name': _('Customer Rating'),
            'type': 'ir.actions.act_window',
            'res_model': 'rating.rating',
            'view_mode': 'list,form',
            'domain': [('res_model', '=', 'helpdesk.ticket'), ('res_id', '=', self.id)],
        }

    # -------------------------------------------------------------------------
    # STAGE EXPANSION FOR KANBAN
    # -------------------------------------------------------------------------

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Always display all stages of the current team in kanban."""
        team_id = self.env.context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('team_ids', '=', False), ('team_ids', 'in', [team_id])]
        else:
            search_domain = []
        return stages.search(search_domain, order=stages._order)

    # -------------------------------------------------------------------------
    # MAIL
    # -------------------------------------------------------------------------

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Create a ticket from incoming email."""
        if custom_values is None:
            custom_values = {}

        # Try to find partner from email
        email_from = msg_dict.get('email_from', '')
        partner = self.env['res.partner'].search([('email', '=', email_from)], limit=1)
        defaults = {
            'name': msg_dict.get('subject', _('No Subject')),
            'partner_id': partner.id if partner else False,
            'partner_email': email_from,
            'description': msg_dict.get('body', ''),
        }
        defaults.update(custom_values)
        return super().message_new(msg_dict, custom_values=defaults)

    def message_update(self, msg_dict, update_vals=None):
        """Update ticket from follow-up email."""
        # Track first response from an agent
        if not self.date_first_response and self.env.user != self.env.ref('base.user_root'):
            if msg_dict.get('author_id') != self.partner_id.id:
                self.date_first_response = fields.Datetime.now()
        return super().message_update(msg_dict, update_vals=update_vals)

    def _track_template(self, changes):
        res = super()._track_template(changes)
        ticket = self[0]
        if 'stage_id' in changes and ticket.stage_id.template_id:
            res['stage_id'] = (
                ticket.stage_id.template_id,
                {'composition_mode': 'mass_mail'},
            )
        return res

    # -------------------------------------------------------------------------
    # PORTAL
    # -------------------------------------------------------------------------

    def _compute_access_url(self):
        super()._compute_access_url()
        for ticket in self:
            ticket.access_url = f'/my/tickets/{ticket.id}'

    # -------------------------------------------------------------------------
    # CRON
    # -------------------------------------------------------------------------

    @api.model
    def _cron_check_sla(self):
        """Scheduled action: update SLA statuses & send alerts for near-deadline tickets."""
        # Recompute SLA status on all open tickets
        open_tickets = self.search([('is_closed', '=', False), ('sla_deadline', '!=', False)])
        open_tickets._compute_sla_status()

        # Alert team leader for tickets about to breach SLA (within 2 hours)
        now = fields.Datetime.now()
        threshold = now + timedelta(hours=2)
        at_risk = open_tickets.filtered(
            lambda t: t.sla_status == 'ongoing' and t.sla_deadline <= threshold
        )
        for ticket in at_risk:
            if ticket.team_id.leader_id:
                ticket.activity_schedule(
                    'mail.mail_activity_data_warning',
                    user_id=ticket.team_id.leader_id.id,
                    note=_('SLA deadline approaching for ticket %s', ticket.number),
                )

    @api.model
    def _cron_auto_close_tickets(self):
        """Auto-close tickets that have been inactive for 7 days in a closing-eligible stage."""
        # Find tickets with last message older than 7 days in stages just before closing
        limit_date = fields.Datetime.now() - timedelta(days=7)
        stale_tickets = self.search([
            ('is_closed', '=', False),
            ('write_date', '<', limit_date),
            ('kanban_state', '=', 'done'),  # Only if marked ready
        ])
        for ticket in stale_tickets:
            ticket.action_close_ticket()
            ticket.message_post(
                body=_('This ticket was automatically closed after 7 days of inactivity.'),
                message_type='notification',
            )
