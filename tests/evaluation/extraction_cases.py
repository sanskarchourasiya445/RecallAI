"""
Phase 7 Extraction & Conversation Evaluation Cases.
Defines ground-truth targets for:
- Action items (tasks, owners, deadlines, unassigned normalization)
- Confirmed decisions vs. rejected proposals/debates
- Open dilemmas vs. resolved questions
- Multi-turn conversational follow-up sequences
"""

EXTRACTION_GROUND_TRUTH = {
    "fixture_1": {
        "expected_action_items": [
            {
                "task": "Prepare and distribute complete PostgreSQL migration plan",
                "owner": "Rahul",
                "deadline": "Friday at 5 PM",
                "status": "Open",
            },
            {
                "task": "Upgrade staging cluster to Kubernetes v1.30",
                "owner": "Sarah",
                "deadline": "Next Tuesday",
                "status": "Open",
            },
            {
                "task": "Update database indexing scripts for new schema changes",
                "owner": None,  # Explicitly unassigned in transcript
                "deadline": None,
                "status": "Open",
            }
        ],
        "expected_key_decisions": [
            "Migrate primary transactional database from MySQL to PostgreSQL",
            "Deploy PgBouncer as sidecar proxy configured with pool size of 50 connections",
            "Upgrade production clusters to Kubernetes version 1.30",
        ],
        "discussions_not_decisions": [
            "Using Redis for session caching instead of Memcached (tabled for Q4)",
            "Hiring external contractor firm for database cutover (evaluated and rejected)",
        ],
        "expected_open_questions": [
            "Which primary AWS deployment region (eu-west-1 vs us-east-1) will be selected for EU data residency compliance?",
            "Who will own long-term database operations and on-call rotations after cutover (platform team or application engineering team)?",
        ],
        "resolved_questions": [
            "Why was the CI/CD pipeline failing on pull requests? (Resolved: Docker layer cache cleared and disk quota increased)"
        ]
    },

    "fixture_2": {
        "expected_action_items": [
            {
                "task": "Implement Razorpay webhook signature verification and payout handlers",
                "owner": "Priya",
                "deadline": "October 15th",
                "status": "Open",
            },
            {
                "task": "Prepare PCI-DSS compliance self-assessment questionnaire and evidence binder",
                "owner": "Marcus",
                "deadline": "October 20th",
                "status": "Open",
            },
            {
                "task": "Benchmark integration costs between Stripe Tax and Avalara for APAC compliance",
                "owner": None,  # Explicitly unassigned
                "deadline": "Before sprint 42",
                "status": "Open",
            }
        ],
        "expected_key_decisions": [
            "Adopt Stripe as primary payment processor for European and US customer transactions",
            "Integrate Razorpay specifically for Indian rupee transactions and UPI",
            "Enforce strict refund turnaround SLA of 24 hours for automated refund requests",
            "Do not support cryptocurrency payments via Coinbase or BitPay",
        ],
        "discussions_not_decisions": [
            "Supporting cryptocurrency checkout (rejected due to low demand and accounting complexity)",
            "Adyen evaluation (discussed as possibility, Stripe chosen instead)",
        ],
        "expected_open_questions": [
            "Should we adopt Stripe Tax or integrate Avalara for APAC sales tax compliance?",
        ],
        "resolved_questions": [
            "Does Stripe support recurring UPI mandates in India? (Resolved: Razorpay chosen for India)"
        ]
    },

    "fixture_3": {
        "expected_action_items": [
            {
                "task": "Audit third-party native libraries for React Native 0.74 New Architecture compatibility",
                "owner": "Elena",
                "deadline": "Wednesday",
                "status": "Open",
            },
            {
                "task": "Set up Firebase Cloud Messaging sandbox environment and migration test harness",
                "owner": "Carlos",
                "deadline": "Friday",
                "status": "Open",
            }
        ],
        "expected_key_decisions": [
            "Enforce strict cold app start threshold of under 1.8 seconds for release 4.2",
            "Upgrade to React Native 0.74 with New Architecture (Fabric renderer and TurboModules) enabled",
            "Switch push notification service from OneSignal to Firebase Cloud Messaging",
        ],
        "discussions_not_decisions": [
            "Rewriting mobile navigation layer in native SwiftUI and Jetpack Compose (rejected)",
            "Introducing tablet-specific split view layouts (tabled until Q1 next year)",
        ],
        "expected_open_questions": [
            "How will the offline queue handle conflict resolution for draft comments during network switches?",
        ],
        "resolved_questions": []
    }
}

CONVERSATIONAL_CASES = [
    {
        "id": "conv_seq_01",
        "fixture_id": "fixture_1",
        "turns": [
            {
                "turn": 1,
                "user_query": "What database did the team choose?",
                "expected_resolved_query_keywords": ["database", "choose"],
                "expected_answer_keywords": ["PostgreSQL"],
                "expected_behavior": "answer",
            },
            {
                "turn": 2,
                "user_query": "Who is responsible for it?",
                "expected_resolved_query_keywords": ["responsible", "PostgreSQL"],
                "expected_answer_keywords": ["Rahul"],
                "expected_behavior": "answer",
            },
            {
                "turn": 3,
                "user_query": "When is it due?",
                "expected_resolved_query_keywords": ["due", "migration"],
                "expected_answer_keywords": ["Friday", "5 PM"],
                "expected_behavior": "answer",
            },
            {
                "turn": 4,
                "user_query": "What is the budget for it?",
                "expected_resolved_query_keywords": ["budget", "PostgreSQL"],
                "expected_answer_keywords": ["could not find", "not mentioned"],
                "expected_behavior": "no_answer",
            }
        ]
    },
    {
        "id": "conv_seq_02",
        "fixture_id": "fixture_2",
        "turns": [
            {
                "turn": 1,
                "user_query": "Which payment provider was chosen for India?",
                "expected_resolved_query_keywords": ["payment", "India"],
                "expected_answer_keywords": ["Razorpay"],
                "expected_behavior": "answer",
            },
            {
                "turn": 2,
                "user_query": "Who will implement the webhook for it?",
                "expected_resolved_query_keywords": ["webhook", "Razorpay"],
                "expected_answer_keywords": ["Priya"],
                "expected_behavior": "answer",
            },
            {
                "turn": 3,
                "user_query": "When does she need to finish it?",
                "expected_resolved_query_keywords": ["finish", "October"],
                "expected_answer_keywords": ["October 15", "October 15th"],
                "expected_behavior": "answer",
            }
        ]
    }
]
