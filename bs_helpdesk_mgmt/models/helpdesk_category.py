# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HelpdeskCategory(models.Model):
    _name = 'helpdesk.category'
    _description = 'Helpdesk Ticket Category'
    _order = 'sequence, name'

    name = fields.Char('Category Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    parent_id = fields.Many2one(
        'helpdesk.category', string='Parent Category',
        index=True, ondelete='cascade',
    )
    child_ids = fields.One2many('helpdesk.category', 'parent_id', string='Subcategories')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    description = fields.Text('Description', translate=True)
    ticket_count = fields.Integer('Ticket Count', compute='_compute_ticket_count')

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            [('category_id', 'in', self.ids)],
            ['category_id'],
            ['__count'],
        )
        mapped_data = {category.id: count for category, count in ticket_data}
        for category in self:
            category.ticket_count = mapped_data.get(category.id, 0)

    def action_view_tickets(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,kanban,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }
