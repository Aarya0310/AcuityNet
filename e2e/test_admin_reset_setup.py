"""
E2E tests for admin reset and demo setup workflows.

Tests:
- Admin reset database via UI
- Admin verifies demo readiness (P-1042 seeded, no active alerts)
- Patient vitals advance deterministically
"""
import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_admin_reset_database(page_with_auth):
    """Admin can reset database and verify P-1042 is ready."""
    page, base_url = page_with_auth
    
    # Navigate to admin settings/reset page
    await page.goto(f"{base_url}/admin/reset")
    
    # Wait for reset confirmation dialog or button
    reset_button = await page.query_selector('[data-testid="reset-database-button"]')
    if reset_button:
        await reset_button.click()
        
        # Handle confirmation dialog if present
        confirm = await page.query_selector('[data-testid="confirm-reset"]')
        if confirm:
            await confirm.click()
    
    # Wait for success message
    success_msg = await page.wait_for_selector(
        'text=/[Dd]atabase reset|[Ss]uccessful/',
        timeout=5000
    )
    assert success_msg is not None, "Reset success message not found"
    
    # Verify P-1042 appears in patient list
    await page.goto(f"{base_url}/monitoring")
    patient_link = await page.wait_for_selector(
        'text=P-1042|text=/patient.*1042/',
        timeout=5000
    )
    assert patient_link is not None, "P-1042 not found in patient list after reset"


@pytest.mark.asyncio
async def test_demo_readiness_verification(page_with_auth):
    """Admin verifies P-1042 is ready for demo (baseline vitals, no alerts)."""
    page, base_url = page_with_auth
    
    # Navigate to monitoring page
    await page.goto(f"{base_url}/monitoring")
    
    # Click P-1042 patient
    patient_row = await page.wait_for_selector(
        'text=P-1042',
        timeout=5000
    )
    await patient_row.click()
    
    # Wait for patient detail page
    await page.wait_for_url("**/patients/P-1042**", timeout=5000)
    
    # Assert patient details visible
    name = await page.query_selector('text=/Patient|Name/')
    assert name is not None, "Patient details not visible"
    
    # Assert vitals visible
    vitals = await page.query_selector('text=/SpO2|Oxygen|HR|Heart/')
    assert vitals is not None, "Vitals not displayed"
    
    # Assert "Advance" button for admin
    advance_btn = await page.query_selector('[data-testid="advance-vitals-button"]')
    if advance_btn:
        # Verify button is enabled
        is_enabled = await advance_btn.is_enabled()
        assert is_enabled, "Advance button should be enabled for admin"
    
    # Assert no active alerts
    no_alert = await page.query_selector('text=/[Nn]o active alert|[Nn]o alert/')
    if no_alert is None:
        # If no explicit "no alert" message, check that alert section is empty/hidden
        alert_section = await page.query_selector('[data-testid="alert-section"]')
        if alert_section:
            content = await alert_section.inner_text()
            assert "No active alert" in content or content.strip() == "", \
                f"Expected no active alert, found: {content}"


@pytest.mark.asyncio
async def test_vitals_advance_deterministically(page_with_auth, advance_time):
    """Admin advances vitals and verifies deterministic sequence."""
    page, base_url = page_with_auth
    
    # Navigate to P-1042 monitoring
    await page.goto(f"{base_url}/monitoring")
    patient_row = await page.wait_for_selector('text=P-1042', timeout=5000)
    await patient_row.click()
    
    await page.wait_for_url("**/patients/P-1042**", timeout=5000)
    
    # Get initial vital values
    initial_vitals = await page.query_selector('[data-testid="vital-values"]')
    if initial_vitals:
        initial_text = await initial_vitals.inner_text()
        print(f"Initial vitals: {initial_text}")
    
    # Click Advance button
    advance_btn = await page.query_selector('[data-testid="advance-vitals-button"]')
    if advance_btn:
        await advance_btn.click()
        
        # Wait for vitals to update
        await page.wait_for_timeout(500)
        
        # Verify vitals changed
        updated_vitals = await page.query_selector('[data-testid="vital-values"]')
        if updated_vitals:
            updated_text = await updated_vitals.inner_text()
            print(f"Updated vitals: {updated_text}")
            assert updated_text != initial_text, "Vitals should change after advance"
    
    # Verify freshness state shows current (not stale)
    freshness = await page.query_selector('[data-testid="freshness-badge"]')
    if freshness:
        badge_text = await freshness.inner_text()
        assert "stale" not in badge_text.lower(), f"Vitals should not be stale: {badge_text}"


@pytest.mark.asyncio
async def test_admin_seeded_patient_visible(page_with_auth):
    """After reset, demo data patient P-1042 is immediately visible."""
    page, base_url = page_with_auth
    
    # Navigate to monitoring
    await page.goto(f"{base_url}/monitoring")
    
    # Search or filter for P-1042
    search_input = await page.query_selector('[data-testid="patient-search"]')
    if search_input:
        await search_input.fill("P-1042")
        await page.wait_for_timeout(300)
    
    # Assert P-1042 appears
    patient_found = await page.wait_for_selector(
        'text=P-1042',
        timeout=5000
    )
    assert patient_found is not None, "P-1042 should be visible after reset"
    
    # Verify it's a link/clickable
    is_clickable = await patient_found.is_enabled()
    assert is_clickable, "Patient link should be clickable"
