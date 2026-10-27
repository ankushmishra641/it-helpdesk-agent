"""Read-only public tools. Mutations require the authenticated ticket API."""
from src.catalog import catalog
from src.rag import search_knowledge_base, format_citations
def tool_search_knowledge_base(query):
    return format_citations(search_knowledge_base(query))
def tool_check_system_status(service):
    key = service.lower().replace('wi-fi', 'wifi')
    found = next((s for s in catalog()['services'] if key in (s['id'], s['name'].lower())), None)
    return f"Simulated service snapshot: {found['name']} — {found['status']}. {found['note']}" if found else 'Service not found in the demo catalog.'
def tool_reset_password(employee_id='', verified=False):
    return 'GUARDRAIL BLOCKED: this public demo cannot reset passwords. An employee ID or a caller-supplied verification flag is not proof of identity. Use the account-access guide or submit an Identity ticket. No account was changed.'
def tool_create_ticket(summary, priority='Medium', category='General'):
    return 'Open the ticket form to review and confirm this request. No ticket has been created.'
def tool_lookup_ticket(ticket_id):
    return 'Open My tickets to look up tickets belonging to your demo session.'
TOOL_SPECS = [
    {'name': 'search_knowledge_base', 'description': 'Read fictional IT documentation.'},
    {'name': 'check_system_status', 'description': 'Read the labeled simulated service snapshot.'},
]
