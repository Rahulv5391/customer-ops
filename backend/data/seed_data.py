"""Drops, recreates, and seeds the Customer Ops SQLite database with a small,
cross-referentially consistent demo dataset.

Run via:
    uv run python -m data.seed_data
"""

import json
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import models  # noqa: F401 - registers all models on Base.metadata
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.agent import SupportAgent
from app.models.audit_log import ActivityLog
from app.models.customer import Customer
from app.models.data_source import DataSource
from app.models.escalation import Escalation
from app.models.kb_document import KBDocument
from app.models.note import CustomerNote
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket, TicketEvent

random.seed(42)

DEMO_PASSWORD = "password123"


def _days_ago(days: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


# Every directory agent is also a login identity - one merged table
# (Architecture.md §4.7), so every roster entry needs credentials, not just
# a couple of hand-picked demo logins.
AGENT_ROSTER = [
    ("Jordan Lee", "jordan.lee@customerops.demo", "team_lead", "Team Lead", "general", True),
    ("Sam Rivera", "sam.rivera@customerops.demo", "support_agent", "Support Agent", "billing", True),
    ("Priya Nair", "priya.nair@customerops.demo", "support_agent", "Support Agent", "billing", True),
    ("Marcus Chen", "marcus.chen@customerops.demo", "support_agent", "Support Agent", "tech", True),
    ("Alicia Gomez", "alicia.gomez@customerops.demo", "support_agent", "Support Agent", "tech", False),
    ("Noah Kim", "noah.kim@customerops.demo", "support_agent", "Support Agent", "onboarding", True),
    ("Fatima Siddiqui", "fatima.siddiqui@customerops.demo", "support_agent", "Support Agent", "onboarding", True),
    ("Diego Alvarez", "diego.alvarez@customerops.demo", "support_agent", "Support Agent", "general", False),
    ("Emma Clarke", "emma.clarke@customerops.demo", "support_agent", "Support Agent", "billing", True),
    ("Ryan O'Connell", "ryan.oconnell@customerops.demo", "support_agent", "Support Agent", "tech", True),
]


def seed_agents(db) -> list[SupportAgent]:
    print("Seeding Agent Directory...")
    password_hash = hash_password(DEMO_PASSWORD)
    agents = [
        SupportAgent(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role=role,
            role_label=role_label,
            team=team,
            shift_start="09:00" if on_duty else "13:00",
            shift_end="17:00" if on_duty else "21:00",
            on_duty=on_duty,
            extension=str(4400 + i),
            two_factor=(role == "team_lead"),
        )
        for i, (full_name, email, role, role_label, team, on_duty) in enumerate(AGENT_ROSTER)
    ]
    db.add_all(agents)
    db.commit()
    return agents


CUSTOMER_ROSTER = [
    ("Daniel Brooks", "daniel.brooks@acme.com", "Acme Retail", "pro", "active"),
    ("Sarah Connor", "sarah.connor@nova.io", "Nova Robotics", "enterprise", "active"),
    ("Victor Salazar", "victor.salazar@brightpath.com", "BrightPath", "free", "at_risk"),
    ("Linda Okafor", "linda.okafor@meridian.co", "Meridian Co", "pro", "active"),
    ("Robert Hayes", "robert.hayes@outlook.com", None, "free", "inactive"),
    ("Aisha Rahman", "aisha.rahman@fernco.com", "Fern & Co", "enterprise", "active"),
    ("Tomas Beck", "tomas.beck@beckdesign.com", "Beck Design", "pro", "active"),
    ("Olivia Pratt", "olivia.pratt@gmail.com", None, "free", "active"),
    ("Noah Fischer", "noah.fischer@quantalabs.com", "Quanta Labs", "enterprise", "at_risk"),
    ("Priya Menon", "priya.menon@lumen.dev", "Lumen Dev", "pro", "active"),
    ("Carla Jensen", "carla.jensen@yahoo.com", None, "free", "active"),
    ("Marcus Vance", "marcus.vance@vancecorp.com", "Vance Corp", "enterprise", "active"),
    ("Sofia Reyes", "sofia.reyes@reyesretail.com", "Reyes Retail", "pro", "inactive"),
]


def seed_customers(db) -> list[Customer]:
    print("Seeding Customers...")
    customers = [
        Customer(
            full_name=name,
            email=email,
            phone=f"+1-555-01{i:02d}",
            company=company,
            account_tier=tier,
            address_line1=f"{100 + i} Market Street",
            city="Springfield",
            region="CA",
            postal_code=f"940{i:02d}",
            country="USA",
            status=status,
            created_at=_days_ago(60 - i * 3),
        )
        for i, (name, email, company, tier, status) in enumerate(CUSTOMER_ROSTER)
    ]
    db.add_all(customers)
    db.commit()
    return customers


PRODUCTS = [
    ("SKU-1001", "Wireless Mouse", Decimal("24.99")),
    ("SKU-1002", "Mechanical Keyboard", Decimal("89.99")),
    ("SKU-1003", "USB-C Hub", Decimal("34.50")),
    ("SKU-1004", "27in Monitor", Decimal("249.00")),
    ("SKU-1005", "Noise-Cancelling Headphones", Decimal("179.99")),
    ("SKU-1006", "Laptop Stand", Decimal("39.99")),
    ("SKU-1007", "Webcam 1080p", Decimal("59.99")),
]

ORDER_STATUSES = ["placed", "shipped", "delivered", "delivered", "refunded", "cancelled"]


def seed_orders(db, customers: list[Customer]) -> list[Order]:
    print("Seeding Orders...")
    orders = []
    for customer in customers:
        for _ in range(random.randint(0, 3)):
            items_pool = random.sample(PRODUCTS, k=random.randint(1, 3))
            items = [
                OrderItem(
                    sku=sku,
                    product_name=name,
                    quantity=random.randint(1, 2),
                    unit_price=price,
                )
                for sku, name, price in items_pool
            ]
            total = sum((item.quantity * item.unit_price for item in items), Decimal("0.00"))
            order = Order(
                customer_id=customer.id,
                status=random.choice(ORDER_STATUSES),
                total_amount=total,
                currency="USD",
                placed_at=_days_ago(random.uniform(1, 45)),
            )
            order.items = items
            orders.append(order)
    db.add_all(orders)
    db.commit()
    return orders


TICKET_SUBJECTS = [
    ("billing", "Charged twice for last invoice"),
    ("technical", "App crashes on login"),
    ("shipping", "Order hasn't arrived yet"),
    ("account", "Can't reset my password"),
    ("billing", "Requesting refund for order"),
    ("technical", "Integration webhook failing"),
    ("shipping", "Wrong item received"),
    ("account", "Need to update billing email"),
    ("other", "General product feedback"),
    ("technical", "API rate limit questions"),
]

CHANNELS = ["email", "chat", "phone", "social"]
STATUSES = ["unassigned", "in_progress", "pending_qa", "resolved", "closed"]
STATUS_WEIGHTS = [2, 3, 1, 3, 2]
PRIORITIES = ["low", "medium", "high", "urgent"]


def seed_tickets(db, customers: list[Customer], agents: list[SupportAgent]) -> list[Ticket]:
    print("Seeding Tickets & Ticket Events...")
    assignable_agents = [a for a in agents if a.role == "support_agent"]
    tickets = []
    for customer in customers:
        for _ in range(random.randint(1, 3)):
            category, subject = random.choice(TICKET_SUBJECTS)
            status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
            agent = random.choice(assignable_agents)
            created_at = _days_ago(random.uniform(0.2, 14))
            resolved_at = None
            csat_score = None
            if status in ("resolved", "closed"):
                resolved_at = created_at + timedelta(hours=random.uniform(1, 48))
                if random.random() < 0.7:
                    csat_score = round(random.uniform(3.0, 5.0), 1)

            ticket = Ticket(
                customer_id=customer.id,
                channel=random.choice(CHANNELS),
                subject=subject,
                status=status,
                priority=random.choice(PRIORITIES),
                assigned_agent_id=agent.id if status != "unassigned" else None,
                category=category,
                csat_score=csat_score,
                created_at=created_at,
                resolved_at=resolved_at,
            )

            events = [
                TicketEvent(
                    event_type="status_change",
                    actor="AI Assistant",
                    detail=f"Ticket created via {ticket.channel} and classified as {category}.",
                    created_at=created_at,
                )
            ]
            if status != "unassigned":
                events.append(
                    TicketEvent(
                        event_type="reassignment",
                        actor=agent.full_name,
                        detail=f"Assigned to {agent.full_name} ({agent.team} team).",
                        created_at=created_at + timedelta(minutes=15),
                    )
                )
            if status in ("resolved", "closed"):
                events.append(
                    TicketEvent(
                        event_type="status_change",
                        actor=agent.full_name,
                        detail=f"Marked {status} after resolving: {subject.lower()}.",
                        created_at=resolved_at,
                    )
                )
            ticket.events = events
            tickets.append(ticket)
    db.add_all(tickets)
    db.commit()
    return tickets


NOTE_BODIES = [
    "Customer prefers email over phone for follow-ups.",
    "Flagged as high-value account, prioritize response time.",
    "Previously churned once, re-onboarded last quarter.",
    "Requested product roadmap briefing next renewal cycle.",
]


def seed_notes(db, customers: list[Customer]) -> list[CustomerNote]:
    print("Seeding Customer Notes...")
    sampled = random.sample(customers, k=min(6, len(customers)))
    notes = [
        CustomerNote(
            customer_id=customer.id,
            author=random.choice(["Sam Rivera", "Priya Nair", "AI Assistant"]),
            body=random.choice(NOTE_BODIES),
            created_at=_days_ago(random.uniform(1, 30)),
        )
        for customer in sampled
    ]
    db.add_all(notes)
    db.commit()
    return notes


def seed_escalations(db, tickets: list[Ticket], agents: list[SupportAgent]) -> list[Escalation]:
    print("Seeding Escalations...")

    def _pick(category: str | None = None, priorities: tuple[str, ...] | None = None):
        pool = tickets
        if category:
            pool = [t for t in pool if t.category == category]
        if priorities:
            pool = [t for t in pool if t.priority in priorities]
        return pool[0] if pool else random.choice(tickets)

    billing_tickets = [t for t in tickets if t.category == "billing"]

    # Each entry's ticket is picked to actually match its narrative (a
    # refund escalation links to a billing ticket, not a random one), and
    # the retention case is deliberately ticket_id=None - escalations can
    # exist without a specific ticket (a proactive account-level case), and
    # this exercises that nullable path rather than leaving it untested.
    plan = [
        (
            "refund_approval",
            "Refund $85.00 for order outside the 30-day return window",
            "high",
            "pending",
            "Refund Policy v2, Section 2: refunds after 30 days require team-lead approval.",
            None,
            billing_tickets[0] if billing_tickets else _pick(),
        ),
        (
            "sla_exception",
            "Priority-1 ticket exceeded 4h first-response SLA, requesting exception sign-off",
            "urgent",
            "pending",
            "Support SLA Policy v3, Section 2: P1 breaches must be logged for review.",
            None,
            _pick(priorities=("high", "urgent")),
        ),
        (
            "account_credit",
            "Issue $50 account credit for repeated shipping delays",
            "medium",
            "approved",
            "Service Recovery Guidelines, Section 2: credits under $50 may be approved by a team lead.",
            None,
            _pick(category="shipping"),
        ),
        (
            "retention_offer_override",
            "Customer requesting contract cancellation, proposing 20% retention discount",
            "high",
            "pending",
            "Canned Responses - Retention v4: discounts above 15% require team-lead approval.",
            None,
            None,
        ),
        (
            "refund_approval",
            "Full refund requested for damaged item, no return required",
            "medium",
            "rejected",
            "Refund Policy v2, Section 3: damaged-item refunds require photo evidence.",
            "Missing required photo evidence of damage.",
            billing_tickets[1] if len(billing_tickets) > 1 else _pick(),
        ),
    ]

    escalations = []
    for etype, action, priority, status, citation, rejection_note, ticket in plan:
        created_at = _days_ago(random.uniform(1, 10))
        resolved_at = (
            created_at + timedelta(hours=random.uniform(2, 72))
            if status in ("approved", "rejected")
            else None
        )
        escalations.append(
            Escalation(
                ticket_id=ticket.id if ticket else None,
                escalation_type=etype,
                requested_action=action,
                priority=priority,
                status=status,
                policy_citation=citation,
                requested_by=random.choice(agents).full_name,
                created_at=created_at,
                rejection_note=rejection_note,
                resolved_at=resolved_at,
            )
        )
    db.add_all(escalations)
    db.commit()
    return escalations


def _kb_content(sections: list[dict]) -> str:
    return json.dumps({"sections": sections})


KB_DOCUMENTS = [
    dict(
        title="Refund Policy",
        category="policy",
        version="v2",
        source_updated_at="March 2026",
        content_json=_kb_content(
            [
                {
                    "heading": "Standard Refund Window",
                    "content": "Orders may be refunded in full within 30 days of delivery, provided the item is unused or defective.",
                },
                {
                    "heading": "Refunds Outside the Window",
                    "content": "Refund requests made after 30 days require a team-lead approval via the Escalation Queue.",
                },
                {
                    "heading": "Damaged Items",
                    "content": "Damaged-item refunds require photo evidence attached to the ticket before processing.",
                },
            ]
        ),
    ),
    dict(
        title="Support SLA Policy",
        category="sop",
        version="v3",
        source_updated_at="February 2026",
        content_json=_kb_content(
            [
                {
                    "heading": "First Response Targets",
                    "content": "P1 tickets: 4 hours. P2: 12 hours. P3: 24 hours. P4: 48 hours.",
                },
                {
                    "heading": "Breach Handling",
                    "content": "Any P1 breach must be logged as an SLA Exception escalation for review.",
                },
            ]
        ),
    ),
    dict(
        title="Shipping & Delivery FAQ",
        category="faq",
        version="v1",
        source_updated_at="January 2026",
        content_json=_kb_content(
            [
                {
                    "heading": "Standard Delivery Times",
                    "content": "Domestic orders arrive within 5-7 business days. International orders may take 10-15 business days.",
                },
                {
                    "heading": "Lost or Delayed Packages",
                    "content": "If a package is more than 3 business days late, offer to reship or issue a shipping credit.",
                },
            ]
        ),
    ),
    dict(
        title="Account & Security FAQ",
        category="faq",
        version="v1",
        source_updated_at="December 2025",
        content_json=_kb_content(
            [
                {
                    "heading": "Password Resets",
                    "content": "Direct customers to the self-serve reset link; agents cannot reset passwords directly.",
                },
                {
                    "heading": "Updating Billing Email",
                    "content": "Billing email changes require verification of the current email on file before updating.",
                },
            ]
        ),
    ),
    dict(
        title="Canned Responses - Retention",
        category="canned_response",
        version="v4",
        source_updated_at="March 2026",
        content_json=_kb_content(
            [
                {
                    "heading": "Cancellation Save Offer",
                    "content": "Thanks for letting us know. Before you go, we'd like to offer 15% off your next renewal - would that help?",
                },
                {
                    "heading": "Retention Discount Limits",
                    "content": "Discounts above 15% require a team-lead approval via the Escalation Queue (Retention Offer Override).",
                },
            ]
        ),
    ),
]


def seed_kb_documents(db) -> list[KBDocument]:
    print("Seeding Knowledge Base Documents...")
    docs = [KBDocument(**doc) for doc in KB_DOCUMENTS]
    db.add_all(docs)
    db.commit()
    return docs


DATA_SOURCES = [
    ("Zendesk", "zendesk", "healthy", 98, [{"name": "tickets", "rowCount": 4210}, {"name": "customers", "rowCount": 1830}]),
    ("Salesforce CRM", "salesforce", "healthy", 96, [{"name": "accounts", "rowCount": 1204}, {"name": "opportunities", "rowCount": 532}]),
    ("Shopify Order DB", "shopify", "degraded", 72, [{"name": "orders", "rowCount": 8890}, {"name": "line_items", "rowCount": 15310}]),
    ("Slack", "slack", "healthy", 100, [{"name": "channels", "rowCount": 24}, {"name": "messages", "rowCount": 98213}]),
    ("Help Center KB Repo", "kb_repo", "healthy", 100, [{"name": "articles", "rowCount": 5}]),
]


def seed_data_sources(db) -> list[DataSource]:
    print("Seeding Data Sources...")
    data_sources = []
    for name, connector_type, sync_status, health, tables in DATA_SOURCES:
        data_sources.append(
            DataSource(
                name=name,
                connector_type=connector_type,
                sync_status=sync_status,
                sync_health_pct=health,
                tables_schema=json.dumps(tables),
                sync_logs=json.dumps(
                    [
                        {
                            "timestamp": _days_ago(0.1).isoformat(),
                            "status": sync_status,
                            "message": "Scheduled sync "
                            + ("completed." if sync_status == "healthy" else "completed with warnings."),
                            "recordsProcessed": sum(t["rowCount"] for t in tables),
                        }
                    ]
                ),
                last_synced_at=_days_ago(0.1),
            )
        )
    db.add_all(data_sources)
    db.commit()
    return data_sources


def seed_activity_log(db, escalations: list[Escalation]) -> list[ActivityLog]:
    print("Seeding Activity Log...")
    entries = [
        ActivityLog(
            action_type="SEED",
            actor="System",
            entity_type="system",
            entity_id="seed",
            summary="Database seeded with demo dataset.",
        )
    ]
    for escalation in escalations:
        entries.append(
            ActivityLog(
                action_type="ESCALATION_CREATED",
                actor=escalation.requested_by,
                entity_type="escalation",
                entity_id=escalation.id,
                summary=f"Escalation {escalation.escalation_number} ({escalation.escalation_type}) created.",
                created_at=escalation.created_at,
            )
        )
    db.add_all(entries)
    db.commit()
    return entries


def main() -> None:
    print("Re-creating clean database tables with the Customer Ops demo dataset...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        agents = seed_agents(db)
        customers = seed_customers(db)
        seed_orders(db, customers)
        tickets = seed_tickets(db, customers, agents)
        seed_notes(db, customers)
        escalations = seed_escalations(db, tickets, agents)
        seed_kb_documents(db)
        seed_data_sources(db)
        seed_activity_log(db, escalations)

        print(
            f"Database seeded successfully with {len(customers)} customers, "
            f"{len(tickets)} tickets, {len(agents)} agents (each with login credentials), "
            f"{len(escalations)} escalations, {len(KB_DOCUMENTS)} KB documents, "
            f"and {len(DATA_SOURCES)} data sources!"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
