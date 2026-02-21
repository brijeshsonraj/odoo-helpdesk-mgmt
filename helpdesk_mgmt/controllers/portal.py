# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class HelpdeskPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            partner = request.env.user.partner_id
            values['ticket_count'] = request.env['helpdesk.ticket'].search_count([
                ('partner_id', '=', partner.id),
            ])
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_tickets(self, page=1, sortby=None, filterby=None, **kw):
        partner = request.env.user.partner_id
        domain = [('partner_id', '=', partner.id)]
        tickets = request.env['helpdesk.ticket'].search(
            domain, order='create_date desc',
        )
        values = {
            'tickets': tickets,
            'page_name': 'tickets',
            'default_url': '/my/tickets',
        }
        return request.render('helpdesk_mgmt.portal_my_tickets', values)

    @http.route('/my/tickets/<int:ticket_id>', type='http', auth='user', website=True)
    def portal_my_ticket(self, ticket_id, **kw):
        ticket = request.env['helpdesk.ticket'].browse(ticket_id)
        if not ticket.exists() or ticket.partner_id != request.env.user.partner_id:
            return request.redirect('/my/tickets')
        values = {
            'ticket': ticket,
            'page_name': 'ticket',
        }
        return request.render('helpdesk_mgmt.portal_my_ticket', values)

    @http.route('/my/tickets/new', type='http', auth='user', website=True)
    def portal_new_ticket(self, **kw):
        categories = request.env['helpdesk.category'].search([])
        values = {
            'categories': categories,
            'page_name': 'new_ticket',
        }
        return request.render('helpdesk_mgmt.portal_create_ticket', values)

    @http.route('/my/tickets/submit', type='http', auth='user',
                website=True, methods=['POST'], csrf=True)
    def portal_submit_ticket(self, **kw):
        partner = request.env.user.partner_id
        team = request.env['helpdesk.team'].search([], limit=1)

        vals = {
            'name': kw.get('subject', _('New Ticket')),
            'description': kw.get('description', ''),
            'partner_id': partner.id,
            'partner_email': partner.email,
            'team_id': team.id if team else False,
            'priority': kw.get('priority', '1'),
        }

        category_id = kw.get('category_id')
        if category_id:
            vals['category_id'] = int(category_id)

        ticket = request.env['helpdesk.ticket'].sudo().create(vals)

        # Handle file attachment
        attachment = kw.get('attachment')
        if attachment and hasattr(attachment, 'read'):
            file_data = attachment.read()
            if file_data:
                request.env['ir.attachment'].sudo().create({
                    'name': attachment.filename,
                    'datas': base64.b64encode(file_data),
                    'res_model': 'helpdesk.ticket',
                    'res_id': ticket.id,
                })

        return request.redirect(f'/my/tickets/{ticket.id}')
