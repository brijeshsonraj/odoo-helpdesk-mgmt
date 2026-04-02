# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class HelpdeskTicketMerge(models.TransientModel):
    _name = 'helpdesk.ticket.merge'
    _description = 'Merge Helpdesk Tickets'

    ticket_ids = fields.Many2many(
        'helpdesk.ticket', string='Tickets to Merge',
        default=lambda self: self._default_ticket_ids(),
    )
    target_ticket_id = fields.Many2one(
        'helpdesk.ticket', string='Target Ticket',
        help="The ticket that will remain. All other tickets will be merged into this one.",
    )
    merge_description = fields.Boolean(
        'Merge Descriptions', default=True,
        help="Append descriptions from merged tickets to the target ticket.",
    )
    merge_followers = fields.Boolean(
        'Merge Followers', default=True,
        help="Add followers from merged tickets to the target ticket.",
    )
    archive_merged = fields.Boolean(
        'Archive Merged Tickets', default=True,
        help="Archive the merged tickets instead of deleting them.",
    )

    def _default_ticket_ids(self):
        active_ids = self.env.context.get('active_ids', [])
        return [(6, 0, active_ids)]

    @api.onchange('ticket_ids')
    def _onchange_ticket_ids(self):
        if self.ticket_ids:
            # Default to highest priority ticket as target
            self.target_ticket_id = self.ticket_ids.sorted('priority', reverse=True)[0]

    def action_merge(self):
        self.ensure_one()
        if len(self.ticket_ids) < 2:
            raise UserError(_("You need at least 2 tickets to merge."))
        if not self.target_ticket_id:
            raise UserError(_("Please select a target ticket."))
        if self.target_ticket_id not in self.ticket_ids:
            raise UserError(_("The target ticket must be one of the selected tickets."))

        tickets_to_merge = self.ticket_ids - self.target_ticket_id

        # Merge descriptions
        if self.merge_description:
            merged_desc = self.target_ticket_id.description or ''
            for ticket in tickets_to_merge:
                if ticket.description:
                    merged_desc += f'<hr/><p><strong>Merged from {ticket.number}:</strong></p>{ticket.description}'
            self.target_ticket_id.description = merged_desc

        # Merge followers
        if self.merge_followers:
            for ticket in tickets_to_merge:
                self.target_ticket_id.message_subscribe(
                    partner_ids=ticket.message_partner_ids.ids,
                )

        # Merge tags
        all_tags = tickets_to_merge.mapped('tag_ids')
        if all_tags:
            self.target_ticket_id.tag_ids = [(4, tag.id) for tag in all_tags]

        # Post merge log on target
        merged_numbers = ', '.join(tickets_to_merge.mapped('number'))
        self.target_ticket_id.message_post(
            body=_('Merged tickets: %s', merged_numbers),
            message_type='notification',
        )

        # Archive or delete merged tickets
        for ticket in tickets_to_merge:
            ticket.message_post(
                body=_('This ticket was merged into %s', self.target_ticket_id.number),
                message_type='notification',
            )

        if self.archive_merged:
            tickets_to_merge.write({'active': False})
        else:
            tickets_to_merge.unlink()

        # Return to the target ticket
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': self.target_ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
