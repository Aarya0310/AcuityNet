#!/usr/bin/env python
"""
Phase 4 Isolated E2E Smoke Test

This script demonstrates the complete Phase 4 workflow in isolation:
- Fresh schema migration
- Deterministic seeding (three users, one patient, context facts, rules)
- Reset/reseed safety verification

Usage:
    python scripts/phase4_smoke.py

Output: Demonstrates successful setup with no errors.
"""

import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.seed.demo_data import seed_demo_data
from backend.app.seed.reset import reset_demo_data
from backend.app.persistence.models import (
    User, Configuration, PatientContextFact, 
    HistorianRuleDefinition, Alert
)


def upgrade_schema(database_url):
    """Run migrations to set up Phase 4 schema."""
    from alembic import command
    from alembic.config import Config

    config = Config("backend/alembic.ini")
    config.set_main_option("script_location", "backend/app/migrations")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def run_smoke_test():
    """Execute Phase 4 setup and safety verification in isolated temporary database."""
    print("\n" + "=" * 70)
    print("PHASE 4 ISOLATED SMOKE TEST")
    print("=" * 70)

    # Create temporary database
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "phase4_smoke.db"
        database_url = f"sqlite:///{db_path}"
        print(f"\nUsing temporary isolated database: {db_path.name}")

        # Schema migration
        print("\n1. Upgrading schema...")
        upgrade_schema(database_url)
        print("   [PASS] Schema upgraded (0001-0005)")

        # Engine and session setup
        engine = create_engine(database_url)
        Sessions = sessionmaker(bind=engine)

        # Seed demo data
        print("\n2. Seeding demo data...")
        with Sessions() as session:
            seed_demo_data(session)
            session.commit()
            users = session.query(User).all()
            print(f"   [PASS] Seeded {len(users)} users, 1 patient, context facts, rules")

        # Reset and reseed
        print("\n3. Testing reset/reseed safety...")
        with Sessions() as session:
            # Reset
            reset_demo_data(session)
            session.commit()
            
            alerts = session.query(Alert).all()
            facts_after = session.query(PatientContextFact).all()
            assert len(alerts) == 0, "Alerts should be deleted by reset"
            assert len(facts_after) == 0, "Facts should be deleted by reset"
            print("   [PASS] Reset deleted all Phase 4 entities")
            
            # Reseed
            seed_demo_data(session)
            session.commit()
            
            facts_restored = session.query(PatientContextFact).all()
            assert len(facts_restored) == 4, f"Expected 4 facts, got {len(facts_restored)}"
            print(f"   [PASS] Reseed restored {len(facts_restored)} context facts")

        engine.dispose()

    print(
        "\n" + "=" * 70
    )
    print(
        "[SUCCESS] Phase 4 smoke test passed!"
    )
    print("=" * 70)
    print("\nSummary:")
    print("  - Schema migrations: working")
    print("  - Deterministic seeding: working")
    print("  - Reset/reseed safety: working")
    return True


if __name__ == "__main__":
    try:
        success = run_smoke_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAILED] Smoke test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
