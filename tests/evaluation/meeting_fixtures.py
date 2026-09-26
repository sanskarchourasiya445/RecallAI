"""
Phase 7 Evaluation Dataset: Realistic Meeting Fixtures
Contains multi-speaker timestamped meeting transcripts with:
- Multiple topics
- Confirmed decisions vs. rejected proposals/discussions
- Action items (with explicit and missing owners/deadlines)
- Open dilemmas vs. resolved questions
- Technical terminology, numeric metrics, and distractor discussions
"""

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE 1: Backend Platform Migration & Cloud Infrastructure
# ─────────────────────────────────────────────────────────────────────────────
FIXTURE_1_TITLE = "Backend Platform Migration & Cloud Infrastructure Sync"
FIXTURE_1_SOURCE = "fixture_1_backend_migration.wav"
FIXTURE_1_TRANSCRIPT = """
00:00:00 - 00:00:25
Alex: Good morning team. Today we are reviewing our backend infrastructure migration, finalizing database architecture, and reviewing container orchestration. Let's make sure we come out with clear ownership.

00:00:25 - 00:00:55
Alex: By the way, Sarah, did you get a chance to go skiing in Tahoe over the weekend?
Sarah: Yes, the snow was fantastic! But let's dive into the architecture before we get distracted.

00:00:55 - 00:01:40
Sarah: Let's start with our primary database. After extensive benchmarking comparing MySQL 8 and PostgreSQL 16 under high concurrency, our team decided to migrate our primary transactional database from MySQL to PostgreSQL. The write performance and JSON indexing in Postgres outperformed MySQL by nearly 40%.

00:01:40 - 00:02:15
Michael: That's confirmed then. For connection management, we also agreed to deploy PgBouncer as a sidecar proxy configured with a pool size of 50 connections per replica to prevent connection starvation during peak traffic.

00:02:15 - 00:02:45
David: Should we consider using Redis for session caching instead of our current Memcached cluster?
Sarah: I think Redis might have advantages for pub/sub, but right now Memcached is completely stable and our memory footprint is low. Let's table Redis for Q4 and keep Memcached as-is for now.

00:02:45 - 00:03:25
Michael: Someone proposed hiring an external contractor firm to handle the entire database cutover over a weekend. We evaluated their proposal, but we decided against it because our in-house team needs deep familiarity with the failover playbooks.

00:03:25 - 00:04:00
Alex: Understood. Let's assign tasks. Rahul, can you take ownership of the database migration?
Rahul: Yes, I will prepare and distribute the complete PostgreSQL migration plan by Friday at 5 PM.

00:04:00 - 00:04:35
Sarah: On the Kubernetes side, we decided to upgrade our production clusters to Kubernetes version 1.30. I will upgrade the staging cluster to v1.30 by next Tuesday to validate our ingress controllers.

00:04:35 - 00:05:10
David: We also noticed the CI/CD pipeline was failing intermittently on pull requests this morning. Why was that happening?
Michael: That was due to a full Docker layer cache volume on the runner. I cleared the orphaned builder cache and increased the runner disk quota 30 minutes ago, so the CI builds are completely green now.

00:05:10 - 00:05:45
Alex: Glad that's resolved. Now, what about our primary AWS deployment region? We evaluated eu-west-1 and us-east-1, but our compliance team hasn't finalized the EU data residency requirements yet. So no final AWS region was selected during this meeting.

00:05:45 - 00:06:20
Rahul: That brings up another open dilemma: who will own long-term database operations and on-call rotations after the cutover? The platform team or the application engineering team? We need to resolve this ownership question with leadership before cutover.

00:06:20 - 00:06:50
Sarah: One last item: someone needs to update the database indexing scripts for the new schema changes, but we don't have an owner assigned for that yet. Let's find an owner in tomorrow's standup.
Alex: Agreed. Thanks everyone, meeting adjourned.
"""

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE 2: Billing & Fintech Payment Architecture
# ─────────────────────────────────────────────────────────────────────────────
FIXTURE_2_TITLE = "Billing & Global Payment Processor Architecture"
FIXTURE_2_SOURCE = "fixture_2_billing_architecture.wav"
FIXTURE_2_TRANSCRIPT = """
00:00:00 - 00:00:20
Priya: Welcome everyone. In this session, we need to finalize our international payment gateway partners, set our refund turnaround SLA, and review compliance timelines.

00:00:20 - 00:00:45
Marcus: Quick side note before we start—the catering team just dropped off lunch boxes in the breakroom for whoever wants them.
Priya: Thanks Marcus, let's keep this session focused so we can grab lunch on time.

00:00:45 - 00:01:30
Priya: First topic: global processing. We evaluated Stripe, Adyen, and Braintree. Based on integration velocity and our current stack, we decided to adopt Stripe as our primary payment processor for European and US customer transactions.

00:01:30 - 00:02:10
Marcus: What about our expansion into the Indian market? Stripe's domestic support in India has regulatory limits with recurring mandates.
Priya: Exactly. We decided to integrate Razorpay specifically for all Indian rupee transactions to support UPI and domestic cards seamlessly.

00:02:10 - 00:02:45
Marcus: Someone suggested we could also support cryptocurrency checkout via Coinbase Commerce or BitPay.
Priya: We reviewed crypto payments, but customer demand is under 0.5% and the accounting reconciliation is too complex. We firmly decided not to support cryptocurrency payments.

00:02:45 - 00:03:25
Priya: For our customer service standards, we decided to enforce a strict refund turnaround SLA of 24 hours for all automated refund requests. The finance team has already approved this policy.

00:03:25 - 00:04:05
Marcus: That's great. Regarding our compliance requirements, our annual PCI-DSS Level 2 compliance audit deadline is firmly scheduled for October 25th.
Priya: Got it. Marcus, will you own preparing the PCI documentation?
Marcus: Yes, I will prepare the PCI-DSS compliance self-assessment questionnaire and evidence binder by October 20th.

00:04:05 - 00:04:40
Priya: And I will implement the Razorpay webhook signature verification and payout handlers by October 15th.

00:04:40 - 00:05:20
Marcus: What about our sales tax compliance in APAC? Should we use Stripe Tax or integrate an external tax engine like Avalara?
Priya: That is an open question. Stripe Tax handles EU VAT and US state sales tax well, but we don't know if its coverage for APAC GST is sufficient. We need to benchmark integration costs before sprint 42. No owner has been assigned to this benchmark yet.

00:05:20 - 00:05:50
Priya: Alright, so Razorpay by Oct 15th, PCI package by Oct 20th, and tax engine decision pending. Let's adjourn.
"""

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE 3: Mobile App Performance & Client Architecture
# ─────────────────────────────────────────────────────────────────────────────
FIXTURE_3_TITLE = "Mobile Client Performance & Architecture Sync"
FIXTURE_3_SOURCE = "fixture_3_mobile_performance.wav"
FIXTURE_3_TRANSCRIPT = """
00:00:00 - 00:00:25
Elena: Welcome everyone to our weekly mobile platform architecture sync. Today we are addressing our app startup latency, push notification provider migration, and our React Native upgrade roadmap.

00:00:25 - 00:01:05
Carlos: Let's start with the startup time issue. In our latest release 4.1, cold app launch latency regressed to 3.4 seconds on mid-tier Android devices. After profiling the bundle, we decided to enforce a strict cold app start threshold of under 1.8 seconds for release 4.2.

00:01:05 - 00:01:45
Elena: To achieve that, we decided to upgrade to React Native version 0.74 and enable the New Architecture, including the Fabric renderer and TurboModules. This will eliminate our JavaScript bridge serialization bottlenecks.

00:01:45 - 00:02:20
Carlos: Someone asked if we should rewrite the entire mobile navigation layer using native SwiftUI and Jetpack Compose.
Elena: A native rewrite was proposed, but that would take four months and delay feature delivery. We rejected the native rewrite and confirmed we will remain on React Native.

00:02:20 - 00:03:00
Carlos: Next item: push notifications. OneSignal pricing has increased by 60%, and their SDK size is adding 4MB to our download footprint. We decided to switch our push notification service from OneSignal to Firebase Cloud Messaging.

00:03:00 - 00:03:35
Elena: I will take the native dependency audit. I will audit our third-party native libraries for React Native 0.74 New Architecture compatibility by Wednesday.
Carlos: And I will set up the Firebase Cloud Messaging sandbox environment and migration test harness by Friday.

00:03:35 - 00:04:15
Carlos: Should we introduce tablet-specific split view layouts in this release?
Elena: We debated tablet support, but our telemetry shows tablet users account for less than 2% of active sessions. We decided to table tablet optimization until Q1 next year.

00:04:15 - 00:04:55
Carlos: Here is an unresolved problem: how will our offline queue handle draft comments when the user switches between airplane mode and cellular networks?
Elena: That remains an open dilemma. We don't have a reliable conflict resolution strategy for offline draft comments yet. We need a technical design proposal on this before next sprint.

00:04:55 - 00:05:20
Elena: Great, action items and goals are set. Thank you everyone!
"""

FIXTURES = {
    "fixture_1": {
        "id": "fixture_1",
        "title": FIXTURE_1_TITLE,
        "source": FIXTURE_1_SOURCE,
        "transcript": FIXTURE_1_TRANSCRIPT.strip(),
    },
    "fixture_2": {
        "id": "fixture_2",
        "title": FIXTURE_2_TITLE,
        "source": FIXTURE_2_SOURCE,
        "transcript": FIXTURE_2_TRANSCRIPT.strip(),
    },
    "fixture_3": {
        "id": "fixture_3",
        "title": FIXTURE_3_TITLE,
        "source": FIXTURE_3_SOURCE,
        "transcript": FIXTURE_3_TRANSCRIPT.strip(),
    },
}
