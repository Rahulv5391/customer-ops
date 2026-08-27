"""Imports every model so Base.metadata.create_all() can find them all."""

from app.models.agent import SupportAgent
from app.models.audit_log import ActivityLog
from app.models.customer import Customer
from app.models.data_source import DataSource
from app.models.escalation import Escalation
from app.models.kb_document import KBDocument
from app.models.note import CustomerNote
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket, TicketEvent

__all__ = [
    "SupportAgent",
    "ActivityLog",
    "Customer",
    "DataSource",
    "Escalation",
    "KBDocument",
    "CustomerNote",
    "Order",
    "OrderItem",
    "Ticket",
    "TicketEvent",
]
