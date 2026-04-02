# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    helpdesk_ticket_ids = fields.One2many(
        'helpdesk.ticket', 'partner_id', string='Helpdesk Tickets',
    )
    helpdesk_ticket_count = fields.Integer(
        'Ticket Count', compute='_compute_helpdesk_ticket_count',
    )

    def _compute_helpdesk_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count'],
        )
        mapped_data = {partner.id: count for partner, count in ticket_data}
        for partner in self:
            partner.helpdesk_ticket_count = mapped_data.get(partner.id, 0)

    def action_view_helpdesk_tickets(self):
        self.ensure_one()
        return {
            'name': 'Helpdesk Tickets',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,kanban,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
