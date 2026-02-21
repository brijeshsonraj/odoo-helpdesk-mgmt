# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Helpdesk Management',
    'version': '19.0.1.0.0',
    'category': 'Services/Helpdesk',
    'sequence': 55,
    'summary': 'Full-featured helpdesk ticketing with SLA, portal & analytics for Community Edition',
    'description': """
Helpdesk Management for Odoo Community
=======================================
A full-featured helpdesk & customer support ticket management system
for Odoo 19 Community Edition.

Key Features:
- Multi-team ticket management with configurable stages
- SLA policies with automatic deadline tracking & escalation
- Customer portal for ticket submission and tracking
- Email gateway integration (auto-create tickets from emails)
- Customer satisfaction ratings
- Ticket merging wizard
- Comprehensive dashboards & reporting
- Priority & tag management
- Automatic ticket assignment (round-robin or load balanced)
    """,
    'author': 'Brijesh Sonraj',        # TODO: replace with your real name/company
    'website': 'https://sonrajbrijesh.com',   # TODO: replace with your real website
    'support': 'sonrajbrijesh@gmail.com',   # TODO: replace with your support email
    # --- Odoo Apps pricing (remove 'price'/'currency' for a free module) ---
    'price': 99.00,
    'currency': 'EUR',
    'depends': [
        'base',
        'mail',
        'portal',
        'rating',
        'resource',
        'utm',
    ],
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk_data.xml',
        'data/mail_template_data.xml',
        'data/helpdesk_cron_data.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_team_views.xml',
        'views/helpdesk_stage_views.xml',
        'views/helpdesk_category_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_sla_views.xml',
        'views/res_partner_views.xml',
        'views/helpdesk_portal_templates.xml',
        'views/helpdesk_dashboard_views.xml',
        'wizard/helpdesk_ticket_merge_views.xml',
        'report/helpdesk_ticket_analysis_views.xml',
        'views/helpdesk_menus.xml',
    ],
    'demo': [
        'data/helpdesk_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'helpdesk_mgmt/static/src/css/helpdesk.css',
        ],
    },
}
