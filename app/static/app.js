document.addEventListener('DOMContentLoaded', () => {
    // Form Elements
    const travelForm = document.getElementById('travelForm');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const btnSubmitPlan = document.getElementById('btnSubmitPlan');

    // UI View Containers
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const draftState = document.getElementById('draftState');
    const finalState = document.getElementById('finalState');
    const loadingText = document.getElementById('loadingText');
    const statusBanner = document.getElementById('statusBanner');
    const statusMessage = document.getElementById('statusMessage');

    // Draft Elements
    const draftTitle = document.getElementById('draftTitle');
    const draftMeta = document.getElementById('draftMeta');
    const draftBudget = document.getElementById('draftBudget');
    const draftHotel = document.getElementById('draftHotel');
    const draftTransit = document.getElementById('draftTransit');
    const weatherSummaryText = document.getElementById('weatherSummaryText');
    const scheduleAccordion = document.getElementById('scheduleAccordion');

    // HITL Buttons & Modal Elements
    const btnApprove = document.getElementById('btnApprove');
    const btnModifyModal = document.getElementById('btnModifyModal');
    const btnRejectModal = document.getElementById('btnRejectModal');
    const reviewModal = document.getElementById('reviewModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnCancelModal = document.getElementById('btnCancelModal');
    const btnSubmitReview = document.getElementById('btnSubmitReview');
    const modalTitle = document.getElementById('modalTitle');
    const lblComments = document.getElementById('lblComments');
    const reviewComments = document.getElementById('reviewComments');
    const modFieldsGroup = document.getElementById('modFieldsGroup');
    const modHotel = document.getElementById('modHotel');
    const modBudget = document.getElementById('modBudget');
    const btnDownloadMarkdown = document.getElementById('btnDownloadMarkdown');
    const finalMarkdownContainer = document.getElementById('finalMarkdownContainer');

    // State Variables
    let currentPlanId = null;
    let pendingAction = 'modify'; // 'reject' or 'modify'
    let currentFinalMarkdown = '';

    // Initialize Default Dates
    const today = new Date();
    const nextMonth = new Date(today);
    nextMonth.setDate(today.getDate() + 30);
    const returnDate = new Date(nextMonth);
    returnDate.setDate(nextMonth.getDate() + 5);

    startDateInput.value = nextMonth.toISOString().split('T')[0];
    endDateInput.value = returnDate.toISOString().split('T')[0];

    // Check System Health
    fetch('/health')
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('systemHealthBadge');
            if (data.status === 'healthy') {
                badge.innerHTML = `<i class="fa-solid fa-circle-check"></i> Connected (${data.openai_key_configured ? 'OpenAI AI' : 'Smart Engine'})`;
            }
        })
        .catch(() => {});

    // Handle Form Submit
    travelForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            destination: document.getElementById('destination').value.trim(),
            start_date: startDateInput.value,
            end_date: endDateInput.value,
            budget_range: document.getElementById('budgetRange').value,
            num_travelers: parseInt(document.getElementById('numTravelers').value, 10),
            interests: document.getElementById('interests').value.split(',').map(i => i.trim()).filter(Boolean),
            special_notes: document.getElementById('specialNotes').value.trim() || null
        };

        // Update UI to Loading
        showView('loading');
        updateStepper(1);
        updateStatus('info', 'Research Agent analyzing destination and gathering intelligence...');

        try {
            const res = await fetch('/plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to submit plan');
            }

            const data = await res.json();
            currentPlanId = data.plan_id;
            
            // Poll/fetch current plan state
            fetchPlanDetails(currentPlanId);

        } catch (err) {
            alert(`Error starting trip planner: ${err.message}`);
            showView('empty');
        }
    });

    // Fetch Plan Details
    async function fetchPlanDetails(planId) {
        try {
            const res = await fetch(`/plan/${planId}`);
            if (!res.ok) throw new Error('Plan not found');

            const data = await res.json();
            
            if (data.stage === 'AWAITING_APPROVAL') {
                updateStepper(3);
                updateStatus('warning', 'Plan generated! Human approval required before finalizing.');
                renderDraftPlan(data);
                showView('draft');
            } else if (data.stage === 'FINALIZED') {
                updateStepper(4);
                updateStatus('success', 'Plan successfully finalized and approved.');
                fetchFinalPlan(planId);
            } else {
                // If still processing
                setTimeout(() => fetchPlanDetails(planId), 1500);
            }

        } catch (err) {
            console.error('Fetch plan error:', err);
        }
    }

    // Render Draft Itinerary
    function renderDraftPlan(data) {
        const draft = data.draft_itinerary || {};
        const req = data.request || {};
        const budget = draft.budget_summary || {};
        const breakdown = budget.breakdown_usd || {};

        draftTitle.textContent = `${budget.num_days || 5}-Day Trip to ${req.destination || 'Destination'}`;
        draftMeta.innerHTML = `<i class="fa-solid fa-calendar"></i> ${req.start_date} to ${req.end_date} | <i class="fa-solid fa-user"></i> ${req.num_travelers} Traveler(s) | <i class="fa-solid fa-wallet"></i> ${req.budget_range}`;
        draftBudget.textContent = `Est. Total: $${breakdown.estimated_grand_total || '1,200'} USD`;
        
        draftHotel.textContent = draft.accommodation_recommendation || 'Central Hotel';
        draftTransit.textContent = budget.recommended_transit_mode || 'Public Transport';

        const weather = data.research_summary?.weather_info || {};
        weatherSummaryText.textContent = weather.summary ? `${weather.summary} ${weather.clothing_recommendation || ''}` : 'Favorable weather conditions expected.';

        // Render Day-by-Day Schedule
        scheduleAccordion.innerHTML = '';
        const schedule = draft.daily_schedule || [];

        schedule.forEach(day => {
            const card = document.createElement('div');
            card.className = 'schedule-card';
            card.innerHTML = `
                <div class="schedule-card-header">
                    <h4>${day.date} — Day ${day.day}</h4>
                    <span class="badge badge-success">$${day.estimated_daily_budget_usd || 120} / day</span>
                </div>
                <div class="schedule-details">
                    <div class="schedule-item"><span class="schedule-label">Morning:</span><span>${day.morning}</span></div>
                    <div class="schedule-item"><span class="schedule-label">Lunch:</span><span>${day.lunch}</span></div>
                    <div class="schedule-item"><span class="schedule-label">Afternoon:</span><span>${day.afternoon}</span></div>
                    <div class="schedule-item"><span class="schedule-label">Evening:</span><span>${day.evening}</span></div>
                </div>
            `;
            scheduleAccordion.appendChild(card);
        });
    }

    // HITL Approve Action
    btnApprove.addEventListener('click', () => {
        if (!currentPlanId) return;
        submitReview('approve', null, null);
    });

    // Open Modal for Modify
    btnModifyModal.addEventListener('click', () => {
        pendingAction = 'modify';
        modalTitle.textContent = 'Request Specific Plan Modifications';
        lblComments.textContent = 'Modification Notes (e.g. Swap Day 2 museum for Akihabara)';
        reviewComments.placeholder = 'e.g. Please replace day 2 activity with Tokyo Disneyland';
        modFieldsGroup.classList.remove('hidden');
        reviewModal.classList.remove('hidden');
    });

    // Open Modal for Reject
    btnRejectModal.addEventListener('click', () => {
        pendingAction = 'reject';
        modalTitle.textContent = 'Reject Itinerary with Feedback';
        lblComments.textContent = 'Reason for Rejection (Required)';
        reviewComments.placeholder = 'e.g. Budget is too high, please cut cost by 30%';
        modFieldsGroup.classList.add('hidden');
        reviewModal.classList.remove('hidden');
    });

    // Close Modal
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelModal.addEventListener('click', closeModal);

    function closeModal() {
        reviewModal.classList.add('hidden');
        reviewComments.value = '';
        modHotel.value = '';
        modBudget.value = '';
    }

    // Submit Review Feedback
    btnSubmitReview.addEventListener('click', () => {
        const comments = reviewComments.value.trim();
        if (pendingAction === 'reject' && !comments) {
            alert('Please provide feedback comments when rejecting a plan.');
            return;
        }

        const mods = {};
        if (modHotel.value.trim()) mods['hotel'] = modHotel.value.trim();
        if (modBudget.value.trim()) mods['budget_range'] = modBudget.value.trim();

        closeModal();
        submitReview(pendingAction, comments || null, Object.keys(mods).length > 0 ? mods : null);
    });

    async function submitReview(action, comments, modifications) {
        showView('loading');
        loadingText.textContent = action === 'approve' ? 'Finalizing your approved trip plan...' : 'Planner Agent revising itinerary based on your feedback...';
        updateStepper(2);
        updateStatus('info', 'Processing human feedback in LangGraph state graph...');

        try {
            const res = await fetch(`/plan/${currentPlanId}/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, comments, modifications })
            });

            if (!res.ok) throw new Error('Failed to submit review');
            const data = await res.json();

            if (data.is_finalized || action === 'approve') {
                fetchFinalPlan(currentPlanId);
            } else {
                // If revised, poll details
                setTimeout(() => fetchPlanDetails(currentPlanId), 1500);
            }

        } catch (err) {
            alert(`Error submitting review: ${err.message}`);
            fetchPlanDetails(currentPlanId);
        }
    }

    // Fetch Finalized Plan
    async function fetchFinalPlan(planId) {
        try {
            const res = await fetch(`/plan/${planId}/final`);
            if (!res.ok) throw new Error('Final plan not ready yet');

            const data = await res.json();
            currentFinalMarkdown = data.final_plan_markdown || '';

            finalTitle.textContent = `Finalized Itinerary: ${data.request?.destination || 'Trip'}`;
            finalMarkdownContainer.textContent = currentFinalMarkdown;

            updateStepper(4);
            updateStatus('success', 'Plan finalized! View markdown summary below.');
            showView('final');

        } catch (err) {
            console.error('Final plan fetch error:', err);
        }
    }

    // Export Download Markdown
    btnDownloadMarkdown.addEventListener('click', () => {
        if (!currentFinalMarkdown) return;
        const blob = new Blob([currentFinalMarkdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Trip_Plan_${currentPlanId.substring(0, 8)}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });

    // Helper Functions
    function showView(view) {
        emptyState.classList.add('hidden');
        loadingState.classList.add('hidden');
        draftState.classList.add('hidden');
        finalState.classList.add('hidden');

        if (view === 'empty') emptyState.classList.remove('hidden');
        if (view === 'loading') loadingState.classList.remove('hidden');
        if (view === 'draft') draftState.classList.remove('hidden');
        if (view === 'final') finalState.classList.remove('hidden');
    }

    function updateStepper(activeStepNum) {
        for (let i = 1; i <= 4; i++) {
            const step = document.getElementById(`step${i}`);
            step.classList.remove('step-active', 'step-completed');
            if (i < activeStepNum) {
                step.classList.add('step-completed');
            } else if (i === activeStepNum) {
                step.classList.add('step-active');
            }
        }
    }

    function updateStatus(type, msg) {
        statusBanner.className = `status-banner ${type}`;
        statusMessage.textContent = msg;
    }
});
