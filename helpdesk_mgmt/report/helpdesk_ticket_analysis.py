# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class HelpdeskTicketAnalysis(models.Model):
    _name = 'helpdesk.ticket.analysis'
    _description = 'Helpdesk Ticket Analysis'
    _auto = False
    _order = 'create_date desc'

    name = fields.Char('Subject', readonly=True)
    number = fields.Char('Ticket Number', readonly=True)
    create_date = fields.Datetime('Created On', readonly=True)
    date_closed = fields.Datetime('Closed Date', readonly=True)
    team_id = fields.Many2one('helpdesk.team', 'Team', readonly=True)
    user_id = fields.Many2one('res.users', 'Assigned To', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    stage_id = fields.Many2one('helpdesk.stage', 'Stage', readonly=True)
    category_id = fields.Many2one('helpdesk.category', 'Category', readonly=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', readonly=True)
    is_closed = fields.Boolean('Closed', readonly=True)
    sla_status = fields.Selection([
        ('ongoing', 'Ongoing'),
        ('reached', 'Reached'),
        ('failed', 'Failed'),
    ], string='SLA Status', readonly=True)
    sla_deadline = fields.Datetime('SLA Deadline', readonly=True)
    response_hours = fields.Float('Response Hours', readonly=True)
    close_hours = fields.Float('Close Hours', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    ticket_count = fields.Integer('# of Tickets', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    t.id AS id,
                    t.name AS name,
                    t.number AS number,
                    t.create_date AS create_date,
                    t.date_closed AS date_closed,
                    t.team_id AS team_id,
                    t.user_id AS user_id,
                    t.partner_id AS partner_id,
                    t.stage_id AS stage_id,
                    t.category_id AS category_id,
                    t.priority AS priority,
                    s.is_close AS is_closed,
                    t.sla_status AS sla_status,
                    t.sla_deadline AS sla_deadline,
                    t.response_hours AS response_hours,
                    t.close_hours AS close_hours,
                    t.company_id AS company_id,
                    1 AS ticket_count
                FROM helpdesk_ticket t
                LEFT JOIN helpdesk_stage s ON t.stage_id = s.id
                WHERE t.active = True
            )
        """ % self._table)
