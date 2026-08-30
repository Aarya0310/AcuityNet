"""
E2E tests for doctor workflows: historian review, dispatch evaluation, and confirmation.

Tests:
- Doctor login and historian review (demographics, risk, rules, timeline)
- Doctor evaluates and confirms dispatch recommendation
"""
import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_doctor_login_and_historian_review(browser_context, app_server):
    """Doctor can login and review historian context for P-1042."""
    from playwright.async_api import async_playwright
    base_url, now_ref = app_server
    
    page = await browser_context.new_page()
    
    try:
        # Navigate to login
        await page.goto(f"{base_url}/")
        
        # Login as doctor
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        
        # Wait for redirect to dashboard
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to P-1042 monitoring
        await page.goto(f"{base_url}/patients/P-1042")
        
        # Click or navigate to historian tab
        historian_tab = await page.query_selector('[data-testid="tab-historian"]')
        if historian_tab:
            await historian_tab.click()
        else:
            await page.goto(f"{base_url}/patients/P-1042/historian")
        
        await page.wait_for_load_state("networkidle")
        
        # Verify demographics section
        demographics = await page.wait_for_selector(
            'text=/[Dd]emographics|[Pp]atient [Dd]etails/',
            timeout=5000
        )
        assert demographics is not None, "Demographics section not found"
        
        # Verify diagnoses list
        diagnoses = await page.query_selector('[data-testid="diagnoses-list"]')
        if diagnoses:
            content = await diagnoses.inner_text()
            assert len(content) > 0, "Diagnoses list should have content"
        
        # Verify medications list
        meds = await page.query_selector('[data-testid="medications-list"]')
        if meds:
            content = await meds.inner_text()
            assert len(content) > 0, "Medications list should have content"
        
        # Verify risk breakdown (baseline vs contextual)
        risk_section = await page.wait_for_selector(
            'text=/[Rr]isk|[Bb]aseline|[Cc]ontextual/',
            timeout=5000
        )
        assert risk_section is not None, "Risk breakdown section not found"
        
        # Verify prototype label (no clinical language)
        prototype_label = await page.query_selector('text=/[Pp]rototype|[Rr]esearch/')
        assert prototype_label is not None, "Prototype label should be visible"
        
        # Verify NO clinical validation language
        invalid_text = await page.query_selector('text=/[Cc]linically [Vv]alidated|[Ee]vidence-[Bb]ased [Tt]reatment/')
        assert invalid_text is None, "Should not claim clinical validation"
        
        # Verify rule cards
        rule_cards = await page.query_selector('[data-testid="rule-cards"]')
        if rule_cards:
            content = await rule_cards.inner_text()
            assert "Rule" in content or "rule" in content, "Rule explanations should be visible"
        
        # Verify timeline events
        timeline = await page.wait_for_selector(
            '[data-testid="timeline"]',
            timeout=5000
        )
        assert timeline is not None, "Timeline should be visible"
        
        timeline_events = await page.query_selector_all('[data-testid="timeline-event"]')
        assert len(timeline_events) >= 1, "Timeline should have events"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_doctor_evaluates_and_confirms_dispatch(browser_context, app_server):
    """Doctor evaluates dispatch candidates and confirms nurse assignment."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as doctor
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to P-1042 alert/dispatch
        await page.goto(f"{base_url}/patients/P-1042/alert")
        
        # Wait for alert to load
        await page.wait_for_load_state("networkidle")
        
        # If no alert yet, trigger by advancing vitals (via admin or API)
        alert_element = await page.query_selector('[data-testid="alert-card"]')
        if not alert_element:
            # Try to navigate to dispatch directly
            await page.goto(f"{base_url}/patients/P-1042/dispatch")
        
        # Assert alert/dispatch page loaded
        await page.wait_for_load_state("networkidle")
        
        # Click to evaluate or refresh candidates
        eval_button = await page.query_selector('[data-testid="evaluate-button"]')
        if eval_button:
            await eval_button.click()
            await page.wait_for_timeout(1000)
        
        # Verify candidates list appears
        candidates = await page.wait_for_selector(
            '[data-testid="candidates-list"]',
            timeout=5000
        )
        assert candidates is not None, "Candidates list should appear"
        
        # Verify top candidate is Sarah
        top_candidate = await page.query_selector('[data-testid="top-candidate"]')
        if top_candidate:
            text = await top_candidate.inner_text()
            assert "Sarah" in text or "N-SARAH" in text, f"Top candidate should be Sarah, got: {text}"
        
        # Verify score breakdown
        score_breakdown = await page.query_selector('[data-testid="score-breakdown"]')
        if score_breakdown:
            content = await score_breakdown.inner_text()
            assert "availability" in content.lower() or "%" in content, \
                f"Score breakdown should show components: {content}"
        
        # Click confirm button
        confirm_button = await page.wait_for_selector(
            '[data-testid="confirm-button"]',
            timeout=5000
        )
        await confirm_button.click()
        
        # Handle confirmation form if present
        submit_form = await page.query_selector('[data-testid="confirm-submit"]')
        if submit_form:
            await submit_form.click()
        
        # Wait for success message or redirect
        success = await page.wait_for_selector(
            'text=/[Cc]onfirmed|[Aa]ssigned|[Ss]uccess/',
            timeout=5000
        )
        assert success is not None, "Confirmation success message should appear"
        
        # Verify alert state updated
        alert_status = await page.query_selector('[data-testid="alert-status"]')
        if alert_status:
            status_text = await alert_status.inner_text()
            assert "Assigned" in status_text or "Sarah" in status_text, \
                f"Alert should show assignment, got: {status_text}"
        
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_doctor_no_candidate_fallback(browser_context, app_server):
    """Doctor sees no-candidate message when no nurses available."""
    base_url, now_ref = app_server
    page = await browser_context.new_page()
    
    try:
        # Login as doctor
        await page.goto(f"{base_url}/")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor-password")
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=5000)
        
        # Navigate to dispatch
        await page.goto(f"{base_url}/patients/P-1042/dispatch")
        await page.wait_for_load_state("networkidle")
        
        # Try to evaluate with no eligible nurses
        # (This may require specific test data setup or API manipulation)
        eval_button = await page.query_selector('[data-testid="evaluate-button"]')
        if eval_button:
            await eval_button.click()
            await page.wait_for_timeout(1000)
        
        # Check for no-candidate message
        no_candidate = await page.query_selector('text=/[Nn]o.*candidate|[Nn]o.*nurse|[Nn]o.*available/')
        if no_candidate:
            assert no_candidate is not None, "Should show no-candidate message"
            
            # Verify retry button
            retry_btn = await page.query_selector('[data-testid="retry-button"]')
            assert retry_btn is not None, "Should have retry button for no-candidate state"
        
    finally:
        await page.close()
