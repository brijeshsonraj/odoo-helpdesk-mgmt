# Helpdesk Management for Odoo Community

## Overview

A comprehensive, Enterprise-grade **Helpdesk & Customer Support Ticket Management System** built for Odoo 19.0 Community Edition. This module fills the biggest gap in Community Edition by providing a full-featured helpdesk solution that rivals the Enterprise Helpdesk module.

## Key Features

### Ticket Management
- **Kanban, List, Form, Pivot, Graph, Calendar & Activity views** for complete ticket visibility
- **Automatic ticket numbering** with configurable sequences (HDT-00001)
- **Priority levels**: Low, Medium, High, Urgent with visual indicators
- **Kanban states**: In Progress, Ready, Blocked
- **Ticket merging wizard** — merge duplicate tickets with full history

### Team Management
- **Multiple helpdesk teams** with dedicated members and team leaders
- **Auto-assignment methods**: Manual, Random, or Load Balanced
- **Team dashboard** with real-time KPIs (open/closed/unassigned/SLA failed)
- **Email alias integration** — incoming emails auto-create tickets

### SLA Policies
- **Configurable SLA policies** per team, priority, and category
- **Automatic deadline computation** with weekend exclusion
- **SLA status tracking**: Ongoing / Reached / Failed
- **Automated alerts** when tickets approach SLA breach (via scheduled actions)
- **SLA breach notifications** to team leaders

### Customer Portal
- **Self-service portal** for customers to view and track their tickets
- **Ticket submission form** with category, priority, and file attachment support
- **Communication thread** — customers can reply directly from the portal
- **Customer satisfaction ratings**

### Reporting & Analytics
- **SQL-based analysis view** (pivot, graph, list) for deep ticket insights
- **Metrics tracked**: Response time, Close time, SLA status, ticket volume
- **Filter by team, agent, category, priority, SLA status, time period**
- **Group by any dimension** for management dashboards

### Integration
- **Mail thread & activity** on every ticket (chatter with full history)
- **Email templates** for ticket creation, resolution, and SLA warnings
- **Partner integration** — ticket count badge on customer records
- **Portal mixin** for secure customer access
- **UTM tracking** for marketing attribution
- **Multi-company support**

### Automation
- **Cron job: SLA monitoring** — checks every hour and creates activities for at-risk tickets
- **Cron job: Auto-close** — automatically closes inactive tickets marked "Ready" after 7 days
- **Stage-based email notifications** — configure email templates per stage transition

## Categories & Tags
- **Hierarchical categories** (parent/child) for organized ticket classification
- **Color-coded tags** for quick visual identification
- **Default categories**: General Inquiry, Technical Issue, Billing & Payment, Feature Request
- **Default tags**: Bug, Improvement, Question, Critical

## Security
- **Three access levels**: Portal (customers), Agent (team members), Manager (full access)
- **Record rules**: Agents see only their team's tickets, Managers see all
- **Multi-company record rules** for proper data isolation

## Installation

1. Copy the `helpdesk_mgmt` folder into your Odoo addons directory
2. Restart the Odoo server
3. Go to Apps → Update Apps List
4. Search for "Helpdesk Management" and install

## Configuration

1. **Teams**: Go to Helpdesk → Configuration → Teams to set up your support teams
2. **Stages**: Configure ticket workflow stages (New → In Progress → Waiting → Resolved)
3. **SLA Policies**: Define time targets per priority/category
4. **Email Aliases**: Set up email-to-ticket integration on each team
5. **Categories & Tags**: Organize ticket types for better reporting

## Pricing Strategy (Odoo Store)

- **Suggested retail price**: $99 - $149 per installation
- **Target market**: SMBs using Odoo Community who need customer support capabilities
- **Competitive advantage**: Only comprehensive Community helpdesk module with SLA, portal, email integration, auto-assignment, and analytics
- **Upsell opportunities**: Premium support packages, customization services

## Dependencies

- `base`, `mail`, `portal`, `rating`, `resource`, `utm`

## License

LGPL-3

## Author

Odoo Community Developers
