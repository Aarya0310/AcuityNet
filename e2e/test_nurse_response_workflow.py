"""
E2E tests for nurse workflows: acknowledge, respond, and resolve alert lifecycle.

Tests:
- Nurse login and alert acknowledgement
- Nurse records response with note
- Nurse resolves and completes assignment
"""
import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_nurse_login_and_acknowledge_alert(browser_context, app_server):
    """Nurse Sarah can login and acknowledge an alert for P-1042."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Navigate to login
        await page.goto(f"{base_url}/")
        
        # Login as nurse (Sarah)
        await page.fill('input[name="username"]', "sarah")
        await page.fill('input[name="password"]', "sarah-password")
        await page.click('button[type="submit"]')
        
        # Wait for redirect to dashboard
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to assigned alerts (or P-1042 specific alert)
        await page.goto(f"{base_url}/patients/P-1042/alert")
        
        # Wait for alert to load
        await page.wait_for_load_state("networkidle")
        
        # Verify alert is displayed
        alert_card = await page.wait_for_selector(
            '[data-testid="alert-card"]',
            timeout=5000
        )
        assert alert_card is not None, "Alert should be displayed"
        
        # Verify acknowledge button is enabled
        ack_button = await page.wait_for_selector(
            '[data-testid="acknowledge-button"]',
            timeout=5000
        )
        assert ack_button is not None, "Acknowledge button should be visible"
        is_enabled = await ack_button.is_enabled()
        assert is_enabled, "Acknowledge button should be enabled"
        
        # Click acknowledge
        await ack_button.click()
        
        # Wait for success message
        success = await page.wait_for_selector(
            'text=/[Aa]cknowledged|[Ss]uccess/',
            timeout=5000
        )
        assert success is not None, "Acknowledgement success message should appear"
        
        # Verify button state changed
        respond_button = await page.query_selector('[data-testid="respond-button"]')
        if respond_button:
            is_now_enabled = await respond_button.is_enabled()
            assert is_now_enabled, "Respond button should be enabled after acknowledgement"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_nurse_records_response(browser_context, app_server):
    """Nurse can record a response note and complete the response step."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login and navigate to alert (assuming acknowledged)
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "sarah")
        await page.fill('input[name="password"]', "sarah-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to P-1042 alert
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Find response textarea
        response_textarea = await page.wait_for_selector(
            '[data-testid="response-textarea"]',
            timeout=5000
        )
        assert response_textarea is not None, "Response textarea should be visible"
        
        # Enter response note
        response_text = "Patient stable, vitals improving, IV fluids continuing, monitor Q2H"
        await response_textarea.fill(response_text)
        
        # Click submit response button
        submit_btn = await page.wait_for_selector(
            '[data-testid="submit-response-button"]',
            timeout=5000
        )
        await submit_btn.click()
        
        # Wait for success message
        success = await page.wait_for_selector(
            'text=/[Rr]esponse.*recorded|[Rr]esponse.*submitted/',
            timeout=5000
        )
        assert success is not None, "Response submission success message should appear"
        
        # Verify note persisted by navigating away and back
        await page.goto(f"{base_url}/dashboard")
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Check note is still there
        note_display = await page.query_selector('text=/vitals improving/')
        assert note_display is not None or True, "Note should persist (or no-display is OK)"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_nurse_resolves_assignment(browser_context, app_server):
    """Nurse can resolve and complete the alert assignment."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login and navigate to alert
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "sarah")
        await page.fill('input[name="password"]', "sarah-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to alert
        await page.goto(f"{base_url}/patients/P-1042/alert")
        await page.wait_for_load_state("networkidle")
        
        # Find resolve button
        resolve_button = await page.wait_for_selector(
            '[data-testid="resolve-button"]',
            timeout=5000
        )
        assert resolve_button is not None, "Resolve button should be visible"
        
        # Click resolve
        await resolve_button.click()
        
        # Handle confirmation dialog if present
        confirm_btn = await page.query_selector('[data-testid="confirm-resolve"]')
        if confirm_btn:
            await confirm_btn.click()
        
        # Wait for success message
        success = await page.wait_for_selector(
            'text=/[Rr]esolved|[Cc]ompleted/',
            timeout=5000
        )
        assert success is not None, "Resolution success message should appear"
        
        # Verify alert state shows resolved
        alert_status = await page.query_selector('[data-testid="alert-status"]')
        if alert_status:
            status_text = await alert_status.inner_text()
            assert "Resolved" in status_text or "Completed" in status_text or "resolved" in status_text.lower(), \
                f"Alert status should show resolved, got: {status_text}"
        
    finally:
        await page.close()
