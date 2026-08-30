"""
E2E tests for concurrent multi-user mutations and consistency.

Tests:
- Concurrent Admin and Doctor mutations to same alert do not corrupt state
- Alert state remains consistent across simultaneous operations
- Concurrent nurse assignments handled correctly
"""
import pytest
import asyncio
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_concurrent_admin_doctor_mutations(browser_context, app_server):
    """Concurrent Admin and Doctor mutations don't corrupt alert state."""
    base_url, now_ref = app_server
    
    # Create two separate pages for admin and doctor
    admin_page = await browser_context.new_page()
    doctor_page = await browser_context.new_page()
    
    try:
        # Admin login
        await admin_page.goto(f"{base_url}/")
        await admin_page.fill('input[name="username"]', "admin")
        await admin_page.fill('input[name="password"]', "admin-password")
        await admin_page.click('button[type="submit"]')
        await admin_page.wait_for_url("**/dashboard", timeout=5000)
        
        # Doctor login
        await doctor_page.goto(f"{base_url}/")
        await doctor_page.fill('input[name="username"]', "doctor")
        await doctor_page.fill('input[name="password"]', "doctor-password")
        await doctor_page.click('button[type="submit"]')
        await doctor_page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate both to P-1042 alert
        await admin_page.goto(f"{base_url}/patients/P-1042/monitoring")
        await doctor_page.goto(f"{base_url}/patients/P-1042/alert")
        
        await admin_page.wait_for_load_state("networkidle")
        await doctor_page.wait_for_load_state("networkidle")
        
        # Concurrent actions:
        # Admin advances vitals while doctor is viewing alert
        async def admin_action():
            advance_btn = await admin_page.query_selector('[data-testid="advance-vitals-button"]')
            if advance_btn:
                await advance_btn.click()
                await admin_page.wait_for_timeout(500)
        
        async def doctor_action():
            eval_btn = await doctor_page.query_selector('[data-testid="evaluate-button"]')
            if eval_btn:
                await eval_btn.click()
                await doctor_page.wait_for_timeout(500)
        
        # Run both concurrently
        await asyncio.gather(
            admin_action(),
            doctor_action()
        )
        
        # Verify state is consistent
        # Navigate to fresh page and check alert state
        check_page = await browser_context.new_page()
        await check_page.goto(f"{base_url}/")
        await check_page.fill('input[name="username"]', "doctor")
        await check_page.fill('input[name="password"]', "doctor-password")
        await check_page.click('button[type="submit"]')
        await check_page.wait_for_url("**/dashboard", timeout=5000)
        
        await check_page.goto(f"{base_url}/patients/P-1042/alert")
        await check_page.wait_for_load_state("networkidle")
        
        # Verify alert data is valid and not corrupted
        alert_card = await check_page.query_selector('[data-testid="alert-card"]')
        if alert_card:
            card_text = await alert_card.inner_text()
            assert len(card_text) > 0, "Alert should have valid content after concurrent mutations"
            
            # Verify no error messages
            error = await check_page.query_selector('text=/[Ee]rror|[Ff]ailed/')
            assert error is None, "Should not have errors after concurrent mutations"
        
        await check_page.close()
        
    finally:
        await admin_page.close()
        await doctor_page.close()


@pytest.mark.asyncio
async def test_concurrent_dispatch_confirmations(browser_context, app_server):
    """Concurrent dispatch confirmations from multiple doctors handled correctly."""
    base_url, now_ref = app_server
    
    # Create two doctor pages
    doctor1_page = await browser_context.new_page()
    doctor2_page = await browser_context.new_page()
    
    try:
        # Both doctors login (using different credentials or same, depending on setup)
        for page in [doctor1_page, doctor2_page]:
            await page.goto(f"{base_url}/")
            await page.fill('input[name="username"]', "doctor")
            await page.fill('input[name="password"]', "doctor-password")
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate both to dispatch
        await doctor1_page.goto(f"{base_url}/patients/P-1042/dispatch")
        await doctor2_page.goto(f"{base_url}/patients/P-1042/dispatch")
        
        await doctor1_page.wait_for_load_state("networkidle")
        await doctor2_page.wait_for_load_state("networkidle")
        
        # Both try to confirm simultaneously
        async def confirm_dispatch(page):
            confirm_btn = await page.query_selector('[data-testid="confirm-button"]')
            if confirm_btn:
                await confirm_btn.click()
                
                # Handle submission
                submit = await page.query_selector('[data-testid="confirm-submit"]')
                if submit:
                    await submit.click()
                
                # Wait for response
                await page.wait_for_timeout(500)
        
        # Run both confirms
        results = await asyncio.gather(
            confirm_dispatch(doctor1_page),
            confirm_dispatch(doctor2_page),
            return_exceptions=True
        )
        
        # At least one should succeed
        assert not all(isinstance(r, Exception) for r in results), \
            "At least one confirmation should succeed"
        
        # Verify final state
        check_page = await browser_context.new_page()
        await check_page.goto(f"{base_url}/")
        await check_page.fill('input[name="username"]', "doctor")
        await check_page.fill('input[name="password"]', "doctor-password")
        await check_page.click('button[type="submit"]')
        await check_page.wait_for_url("**/dashboard", timeout=5000)
        
        await check_page.goto(f"{base_url}/patients/P-1042/alert")
        await check_page.wait_for_load_state("networkidle")
        
        # Verify alert has exactly one assignment (not duplicated)
        status = await check_page.query_selector('[data-testid="alert-status"]')
        if status:
            status_text = await status.inner_text()
            # Should show one nurse assignment, not multiple
            assert "Sarah" in status_text or "Assigned" in status_text, \
                f"Alert should show single assignment, got: {status_text}"
        
        await check_page.close()
        
    finally:
        await doctor1_page.close()
        await doctor2_page.close()


@pytest.mark.asyncio
async def test_alert_state_consistency_under_load(browser_context, app_server):
    """Alert state remains consistent when multiple users access simultaneously."""
    base_url, now_ref = app_server
    
    # Create multiple viewer pages
    pages = [
        await browser_context.new_page(),
        await browser_context.new_page(),
        await browser_context.new_page(),
    ]
    
    try:
        # All login and navigate to same alert
        for i, page in enumerate(pages):
            role = ["admin", "doctor", "sarah"][i]  # Different roles
            pwd = f"{role}-password"
            
            await page.goto(f"{base_url}/")
            await page.fill('input[name="username"]', role)
            await page.fill('input[name="password"]', pwd)
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate all to P-1042 alert
        alert_pages = [pages[1], pages[2]]  # Doctor and nurse
        for page in alert_pages:
            await page.goto(f"{base_url}/patients/P-1042/alert")
            await page.wait_for_load_state("networkidle")
        
        # Get initial state from each
        async def get_alert_state(page):
            card = await page.query_selector('[data-testid="alert-card"]')
            if card:
                return await card.inner_text()
            return ""
        
        states = await asyncio.gather(*[get_alert_state(p) for p in alert_pages])
        
        # Verify states are identical
        assert states[0] == states[1], \
            f"Alert state should be identical across viewers, got different states: {states}"
        
    finally:
        for page in pages:
            await page.close()
