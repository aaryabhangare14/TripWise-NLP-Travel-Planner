// TripWise Client Engine
let sessionId = localStorage.getItem("tripwise_session_id") || "sess_" + Math.random().toString(36).substring(2, 9);
localStorage.setItem("tripwise_session_id", sessionId);

let currentItineraryData = null;
let currentBookingData = null;
let recognition = null;
let isRecording = false;
let chatHistory = JSON.parse(localStorage.getItem("tripwise_history") || "[]");

// Prompt presets for the "Refresh Prompt" button
const promptPresets = [
  [
    {
      title: "Discover places to visit",
      desc: "What are the best attractions and beaches in Goa? Include cultural spots and sunset points.",
      query: "What are the best places to visit in Goa? Include beaches, culture, and cafes.",
      iconClass: "fa-regular fa-compass",
      colorClass: "icon-orange"
    },
    {
      title: "Hotel Suggestions",
      desc: "Can you show me a list of the best boutique resorts and stays in Manali with mountain views?",
      query: "Can you suggest good places to stay in Manali with mountain views and budget options?",
      iconClass: "fa-solid fa-hotel",
      colorClass: "icon-purple"
    },
    {
      title: "Itinerary & Trip Planning",
      desc: "Plan a 4-day trip to Manali for 2 people with ₹20,000 budget. I like adventure and nature.",
      query: "Plan a 4-day trip to Manali for 2 people with ₹20,000 budget. I like adventure and nature.",
      iconClass: "fa-solid fa-plane-departure",
      colorClass: "icon-teal"
    }
  ],
  [
    {
      title: "Discover places to visit",
      desc: "What are the must-see royal palaces and heritage sites in Jaipur for a 3-day holiday?",
      query: "What should I see in Jaipur? Suggest top heritage and cultural attractions.",
      iconClass: "fa-regular fa-compass",
      colorClass: "icon-orange"
    },
    {
      title: "Food & Dining Guide",
      desc: "What are the famous regional street foods and authentic local dishes to try in Kerala?",
      query: "What are the famous cuisines and must-try dishes in Kerala?",
      iconClass: "fa-solid fa-utensils",
      colorClass: "icon-purple"
    },
    {
      title: "Backwaters & Nature",
      desc: "Plan a relaxing 5-day vacation to Kerala under 25k for 2 people. I love nature and houseboats.",
      query: "Plan a 5 day trip to Kerala under 25k for 2 people. I love nature and food.",
      iconClass: "fa-solid fa-water",
      colorClass: "icon-teal"
    }
  ],
  [
    {
      title: "Adventure & Thrills",
      desc: "Plan a 3-day adventure trip to Rishikesh with river rafting and bungee jumping under 12k.",
      query: "Plan a 3-day adventure trip to Rishikesh under 12000 with river rafting and bungee jumping.",
      iconClass: "fa-solid fa-mountain",
      colorClass: "icon-orange"
    },
    {
      title: "Weather & Best Season",
      desc: "What is the best time of year to visit Ladakh, and what is the current climate profile?",
      query: "What is the weather and best time to visit Ladakh?",
      iconClass: "fa-solid fa-cloud-sun",
      colorClass: "icon-purple"
    },
    {
      title: "Ticket Booking & Invoice",
      desc: "Confirm tickets for a 3-day Goa trip and download official invoice PDF.",
      query: "Plan a 3-day trip to Goa under 15000 and confirm tickets with invoice",
      iconClass: "fa-solid fa-receipt",
      colorClass: "icon-teal"
    }
  ],
  [
    {
      title: "Packing & Gear Tips",
      desc: "What clothes, shoes, and essential gear should I pack for a 4-day trip to Manali in winter?",
      query: "What should I pack for Manali? Give me clothing and gear checklist.",
      iconClass: "fa-solid fa-suitcase-rolling",
      colorClass: "icon-orange"
    },
    {
      title: "Travel Safety & Solo Travel",
      desc: "Is Goa safe for solo female backpackers, and what precautions should I take at night?",
      query: "Is Goa safe for solo female travelers? Give me safety tips.",
      iconClass: "fa-solid fa-shield-halved",
      colorClass: "icon-purple"
    },
    {
      title: "Transport & Route Guide",
      desc: "What is the best way to travel from Delhi to Manali? Are Volvo buses or private cabs better?",
      query: "How to reach Manali from Delhi? Give me transport options.",
      iconClass: "fa-solid fa-route",
      colorClass: "icon-teal"
    }
  ],
  [
    {
      title: "Instagram & Photo Spots",
      desc: "What are the top aesthetic and scenic photography locations in Jaipur for sunrise and sunset?",
      query: "Best photography spots in Jaipur for sunrise and golden hour",
      iconClass: "fa-solid fa-camera",
      colorClass: "icon-orange"
    },
    {
      title: "Shopping & Local Bazaars",
      desc: "What are the best souvenirs and handicrafts to buy in Jaipur, and which bazaars are authentic?",
      query: "What are the best things to buy in Jaipur and famous shopping markets?",
      iconClass: "fa-solid fa-bag-shopping",
      colorClass: "icon-purple"
    },
    {
      title: "Nightlife & Evening Cafes",
      desc: "Where can I find the best beach clubs, sunset parties, and live acoustic music in North Goa?",
      query: "Where is the best nightlife in Goa? Top beach clubs and sunset lounges.",
      iconClass: "fa-solid fa-champagne-glasses",
      colorClass: "icon-teal"
    }
  ],
  [
    {
      title: "Spiritual Ghats & Aarti",
      desc: "Experience holy Ganga Aarti at Dashashwamedh Ghat and sunrise boat rides along ancient stone ghats.",
      query: "Plan a 3-day spiritual trip to Varanasi under 12000 with Ganga Aarti and boat ride",
      iconClass: "fa-solid fa-om",
      colorClass: "icon-orange"
    },
    {
      title: "Himalayan Tea & Toy Train",
      desc: "Tiger Hill sunrise over Mt. Kanchenjunga, UNESCO Himalayan toy train, and emerald tea estate walks.",
      query: "Plan a 4-day trip to Darjeeling with tea gardens and Tiger Hill sunrise",
      iconClass: "fa-solid fa-train-subway",
      colorClass: "icon-purple"
    },
    {
      title: "World Heritage Taj Mahal",
      desc: "Ivory marble Taj Mahal sunrise tour, red-sandstone Agra Fort, and authentic Mughlai street feasts.",
      query: "Plan a 2-day heritage trip to Agra for Taj Mahal under 10000",
      iconClass: "fa-solid fa-monument",
      colorClass: "icon-teal"
    }
  ]
];

let currentPresetIndex = 0;

// Initialize Speech Recognition if supported
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-IN';

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("userInput").value = transcript;
    toggleVoiceInput(false);
    sendMessage(transcript);
  };

  recognition.onerror = () => toggleVoiceInput(false);
  recognition.onend = () => toggleVoiceInput(false);
}

document.addEventListener("DOMContentLoaded", () => {
  renderChatHistory();
  document.getElementById("userInput").focus();
});

function toggleNlpDrawer(forceState) {
  const drawer = document.getElementById("nlpDrawer");
  const backdrop = document.getElementById("nlpDrawerBackdrop");
  const isOpening = forceState !== undefined ? forceState : !drawer.classList.contains("active");

  if (isOpening) {
    drawer.classList.add("active");
    backdrop.classList.add("active");
  } else {
    drawer.classList.remove("active");
    backdrop.classList.remove("active");
  }
}

function triggerPrompt(queryText) {
  document.getElementById("userInput").value = queryText;
  sendMessage(queryText);
}

function cyclePrompts() {
  currentPresetIndex = (currentPresetIndex + 1) % promptPresets.length;
  const cards = promptPresets[currentPresetIndex];
  const container = document.getElementById("heroPromptCards");

  container.innerHTML = cards.map(c => `
    <div class="prompt-action-card" onclick="triggerPrompt('${escapeAttr(c.query)}')">
      <div class="prompt-card-icon ${c.colorClass}">
        <i class="${c.iconClass}"></i>
      </div>
      <div class="prompt-card-text">
        <h4>${c.title}</h4>
        <p>${c.desc}</p>
      </div>
    </div>
  `).join('');
}

function appendInputPrefix(slotType, prefix) {
  const input = document.getElementById("userInput");
  let val = input.value.trim();
  if (val && !val.endsWith(" ")) val += " ";
  input.value = val + prefix;
  input.focus();
}

function handleTextareaKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleFormSubmit(e);
  }
}

function handleFormSubmit(e) {
  if (e) e.preventDefault();
  const input = document.getElementById("userInput");
  const msg = input.value.trim();
  if (!msg) return;
  sendMessage(msg);
}

function openQuickOptions() {
  const options = [
    "Plan 3 days in Goa under 15k",
    "Plan 4 days in Manali for 2 people",
    "Confirm booking for this trip",
    "Download invoice PDF",
    "Suggest destinations under 20k",
    "Remove beaches and add historical spots"
  ];
  const choice = prompt("Choose a quick request or type your query:\n\n" + options.map((o, idx) => `${idx + 1}. ${o}`).join("\n"));
  if (choice) {
    const num = parseInt(choice);
    if (!isNaN(num) && num >= 1 && num <= options.length) {
      triggerPrompt(options[num - 1]);
    } else {
      triggerPrompt(choice);
    }
  }
}

function openCreateTripPrompt() {
  const dest = prompt("Which destination would you like to plan a trip for? (e.g. Goa, Manali, Kerala, Jaipur, Agra, Varanasi, Darjeeling, Ladakh, Rishikesh)");
  if (dest) {
    triggerPrompt(`Plan a 3-day trip to ${dest.trim()}`);
  }
}

function toggleVoiceInput(forcedState) {
  const btn = document.getElementById("btnMic");
  if (!recognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
    return;
  }

  isRecording = forcedState !== undefined ? forcedState : !isRecording;
  if (isRecording) {
    btn.classList.add("recording");
    try { recognition.start(); } catch (e) {}
  } else {
    btn.classList.remove("recording");
    try { recognition.stop(); } catch (e) {}
  }
}

async function sendMessage(text) {
  const input = document.getElementById("userInput");
  input.value = "";

  // Hide welcome hero on first message
  const hero = document.getElementById("welcomeHero");
  if (hero) hero.style.display = "none";

  // Append user message
  appendUserMessage(text);

  // Update session title & history
  document.getElementById("chatSessionTitle").textContent = text.length > 28 ? text.substring(0, 25) + "..." : text;
  saveToChatHistory(text);

  // Show typing indicator
  showTyping(true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId })
    });

    const data = await res.json();
    showTyping(false);

    if (data.error && !data.reply) {
      appendBotMessage("An error occurred: " + data.error);
      return;
    }

    if (data.itinerary) {
      currentItineraryData = data.itinerary;
    }
    if (data.booking_confirmation) {
      currentBookingData = data.booking_confirmation;
    }

    appendBotMessage(
      data.reply,
      data.itinerary,
      data.booking_confirmation,
      data.suggested_destinations,
      data.quick_replies
    );

    if (data.session_state) {
      updateSessionStateUI(data.session_state);
    }
    if (data.nlp_trace) {
      updateNlpInspectorUI(data.nlp_trace);
    }

  } catch (err) {
    showTyping(false);
    appendBotMessage("Network connection error. Please verify the Flask server is running.");
    console.error(err);
  }
}

function appendUserMessage(text) {
  const container = document.getElementById("messagesContainer");
  const row = document.createElement("div");
  row.className = "chat-bubble-row user-row";
  row.innerHTML = `<div class="bubble-user">${escapeHtml(text)}</div>`;
  container.appendChild(row);
  scrollToBottom();
}

function appendBotMessage(replyText, itinerary = null, bookingConfirmation = null, suggestedDestinations = null, quickReplies = []) {
  const container = document.getElementById("messagesContainer");
  const row = document.createElement("div");
  row.className = "chat-bubble-row bot-row";

  const parsedText = formatMarkdown(replyText);

  let confirmationHtml = "";
  if (bookingConfirmation) {
    confirmationHtml = renderBookingConfirmationCard(bookingConfirmation);
  }

  let itineraryHtml = "";
  if (itinerary && itinerary.itinerary_days && itinerary.itinerary_days.length > 0) {
    itineraryHtml = renderItineraryCard(itinerary);
  }

  let suggestionsHtml = "";
  if (suggestedDestinations && suggestedDestinations.length > 0) {
    suggestionsHtml = renderDestinationSuggestions(suggestedDestinations);
  }

  let quickRepliesHtml = "";
  if (quickReplies && quickReplies.length > 0) {
    quickRepliesHtml = `
      <div class="quick-reply-bar">
        ${quickReplies.map(qr => {
          if (qr.includes("Download Invoice")) {
            return `<button class="quick-btn btn-highlight" onclick="downloadInvoiceDirect()"><i class="fa-solid fa-file-pdf"></i> Download Invoice PDF</button>`;
          }
          return `<button class="quick-btn" onclick="triggerPrompt('${escapeAttr(qr)}')">${escapeHtml(qr)}</button>`;
        }).join('')}
      </div>
    `;
  }

  row.innerHTML = `
    <div class="bubble-bot">
      ${parsedText}
      ${confirmationHtml}
      ${itineraryHtml}
      ${suggestionsHtml}
      ${quickRepliesHtml}
    </div>
  `;

  container.appendChild(row);
  scrollToBottom();
}

function renderBookingConfirmationCard(booking) {
  const bookingId = booking.booking_id || "TW-2026-CONFIRMED";
  const downloadUrl = `/api/download_invoice?booking_id=${bookingId}&session_id=${sessionId}&name=${encodeURIComponent(booking.customer_name || 'Ronald')}`;

  return `
    <div class="ticket-confirmation-card">
      <div class="ticket-badge-ribbon">
        <i class="fa-solid fa-circle-check"></i> OFFICIAL BOOKING CONFIRMED
      </div>
      
      <div class="ticket-header-row">
        <div>
          <span class="ticket-ref-label">Booking Reference:</span>
          <h3 class="ticket-ref-code">${bookingId}</h3>
        </div>
        <div class="ticket-status-stamp">
          <i class="fa-solid fa-shield-check"></i> ISSUED
        </div>
      </div>

      <div class="ticket-details-grid">
        <div class="ticket-detail-item">
          <span class="detail-label">Lead Passenger</span>
          <strong>${booking.customer_name || 'Ronald'}</strong>
        </div>
        <div class="ticket-detail-item">
          <span class="detail-label">Destination</span>
          <strong>${booking.destination}</strong>
        </div>
        <div class="ticket-detail-item">
          <span class="detail-label">Travel Dates</span>
          <strong>${booking.start_date} – ${booking.end_date}</strong>
        </div>
        <div class="ticket-detail-item">
          <span class="detail-label">Total Paid (Tax Incl.)</span>
          <strong class="ticket-price">₹${(booking.total_amount || 0).toLocaleString()}</strong>
        </div>
      </div>

      <div class="ticket-inclusions-row">
        <span class="inclusion-pill"><i class="fa-solid fa-hotel"></i> Resort Stay Included</span>
        <span class="inclusion-pill"><i class="fa-solid fa-car"></i> Airport/Station Transfers</span>
        <span class="inclusion-pill"><i class="fa-solid fa-ticket"></i> Sightseeing Passes</span>
      </div>

      <div class="ticket-actions-bar">
        <a href="${downloadUrl}" class="btn-download-invoice" target="_blank" download>
          <i class="fa-solid fa-file-pdf"></i> Download Official Invoice (PDF)
        </a>
        <button class="btn-print-ticket" onclick="window.print()">
          <i class="fa-solid fa-print"></i> Print Ticket
        </button>
      </div>
    </div>
  `;
}

function renderItineraryCard(itin) {
  const cardId = "itin_" + Math.random().toString(36).substring(2, 7);
  const days = itin.itinerary_days || [];
  const cost = itin.cost_breakdown || {};

  const tabsHtml = days.map((d, idx) => `
    <button class="day-tab-btn ${idx === 0 ? 'active' : ''}" onclick="switchItinDay('${cardId}', ${d.day}, this)">
      Day ${d.day}
    </button>
  `).join('');

  const daysContentHtml = days.map((d, idx) => `
    <div class="day-content" id="${cardId}_day_${d.day}" style="display: ${idx === 0 ? 'flex' : 'none'};">
      <div class="day-date-banner">
        <i class="fa-regular fa-calendar-check"></i>
        <span>${d.title}</span>
      </div>
      ${d.places.map(p => `
        <div class="activity-card">
          <div class="activity-top">
            <span class="activity-time-slot slot-${p.time_slot}">${p.time_slot}</span>
            <span class="activity-time-range"><i class="fa-regular fa-clock"></i> ${p.time_range || 'Flexible'}</span>
            <span class="activity-cost">${p.cost > 0 ? '₹' + p.cost.toLocaleString() + ' / person' : 'Included'}</span>
          </div>
          <div class="activity-name">${p.name}</div>
          <div class="activity-desc">${p.description}</div>
          <div class="activity-footer">
            <span><i class="fa-solid fa-location-dot"></i> ${p.category} &bull; ~${p.duration_hours} hrs</span>
            <span class="activity-rating"><i class="fa-solid fa-star"></i> ${p.rating}</span>
          </div>
        </div>
      `).join('')}
    </div>
  `).join('');

  const budgetDifference = cost.difference || 0;
  let diffLabel = "";
  if (cost.user_budget) {
    if (budgetDifference >= 0) {
      diffLabel = `<span style="color: #15803d; font-size: 0.75rem;">(₹${budgetDifference.toLocaleString()} within budget)</span>`;
    } else {
      diffLabel = `<span style="color: #b91c1c; font-size: 0.75rem;">(₹${Math.abs(budgetDifference).toLocaleString()} above budget)</span>`;
    }
  }

  return `
    <div class="itinerary-card" id="${cardId}">
      <div class="itinerary-header">
        <div>
          <h3><i class="fa-solid fa-map-pin" style="color: #ea580c;"></i> ${itin.destination} &bull; ${itin.duration} Days</h3>
          <div class="itinerary-timeline-meta">
            <span><i class="fa-regular fa-calendar"></i> <b>Start:</b> ${itin.start_date || 'Day 1'} &nbsp;&rarr;&nbsp; <b>End:</b> ${itin.end_date || 'Day ' + itin.duration}</span>
          </div>
          <div class="itinerary-tags">
            <span class="itinerary-tag">${itin.travelers} Traveler${itin.travelers > 1 ? 's' : ''}</span>
            ${(itin.active_interests || []).map(i => `<span class="itinerary-tag">${i}</span>`).join('')}
          </div>
        </div>
      </div>

      <div class="day-tabs">
        ${tabsHtml}
      </div>

      ${daysContentHtml}

      <!-- Cost Summary -->
      <div class="budget-widget">
        <div class="budget-widget-header">
          <h4><i class="fa-solid fa-receipt text-teal"></i> Complete Trip Cost Estimation</h4>
          <span class="budget-status-pill status-${cost.status || 'within'}">
            ${(cost.status || 'within').replace('_', ' ')}
          </span>
        </div>
        <div class="budget-grid">
          <div class="budget-cell">
            <span>Attraction Passes</span>
            <strong>₹${(cost.activities || 0).toLocaleString()}</strong>
          </div>
          <div class="budget-cell">
            <span>Resort Stay (${itin.duration > 1 ? itin.duration - 1 : 1}N)</span>
            <strong>₹${(cost.accommodation || 0).toLocaleString()}</strong>
          </div>
          <div class="budget-cell">
            <span>Meals & Dining</span>
            <strong>₹${(cost.food || 0).toLocaleString()}</strong>
          </div>
          <div class="budget-cell">
            <span>Local Transit</span>
            <strong>₹${(cost.local_transport || 0).toLocaleString()}</strong>
          </div>
        </div>
        <div class="budget-total-row">
          <div>
            <span>Estimated Package Total:</span>
            ${diffLabel}
          </div>
          <strong>₹${(cost.total_estimated || 0).toLocaleString()}</strong>
        </div>
      </div>

      <!-- Action: Book & Confirm Tickets -->
      <div class="itinerary-confirm-action-box">
        <div class="confirm-prompt-text">
          <strong>Ready to confirm your travel plan?</strong>
          <span>Lock in your attraction passes, hotel stay, and download official PDF tax invoice.</span>
        </div>
        <button class="btn-confirm-trip-cta" onclick="confirmBookingCurrentTrip()">
          <i class="fa-solid fa-ticket"></i> Confirm & Book Trip (Get Invoice PDF)
        </button>
      </div>
    </div>
  `;
}

function switchItinDay(cardId, dayNum, btn) {
  const card = document.getElementById(cardId);
  card.querySelectorAll(".day-tab-btn").forEach(b => b.classList.remove("active"));
  card.querySelectorAll(".day-content").forEach(c => c.style.display = "none");

  btn.classList.add("active");
  const target = document.getElementById(`${cardId}_day_${dayNum}`);
  if (target) target.style.display = "flex";
}

async function confirmBookingCurrentTrip() {
  showTyping(true);
  try {
    const res = await fetch("/api/confirm_booking", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, customer_name: "Ronald" })
    });
    const data = await res.json();
    showTyping(false);

    if (data.status === "success" && data.booking) {
      currentBookingData = data.booking;
      appendBotMessage(
        `✅ **Booking Confirmed for ${data.booking.destination}!** Your official travel pass and invoice reference is **${data.booking.booking_id}**. Click the button below to download your complete invoice PDF.`,
        null,
        data.booking,
        null,
        ["Download Invoice PDF", "What to pack?", "Weather forecast"]
      );
    }
  } catch (e) {
    showTyping(false);
    console.error(e);
  }
}

function downloadInvoiceDirect() {
  const bookingId = (currentBookingData && currentBookingData.booking_id) || (currentItineraryData && currentItineraryData.booking_id) || "TW-2026-CONFIRMED";
  const url = `/api/download_invoice?booking_id=${bookingId}&session_id=${sessionId}&name=Ronald`;
  const a = document.createElement("a");
  a.href = url;
  a.download = `TripWise_Invoice_${bookingId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function renderDestinationSuggestions(suggestions) {
  return `
    <div style="margin-top: 12px; display: flex; flex-direction: column; gap: 8px;">
      <h4 style="font-size: 0.85rem; color: #0284c7;">Recommended Destinations:</h4>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
        ${suggestions.map(s => `
          <div class="trend-card" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px;" onclick="triggerPrompt('Plan a 3-day trip to ${s.name}')">
            <strong style="font-size: 0.85rem; color: #0f172a;">${s.name}</strong>
            <p style="font-size: 0.72rem; color: #64748b;">~₹${s.estimated_trip_cost.toLocaleString()} &bull; ${s.state}</p>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function updateSessionStateUI(state) {
  document.getElementById("slotDest").textContent = state.destination || "Not specified";
  document.getElementById("slotDuration").textContent = state.duration ? `${state.duration} Days` : "Not specified";
  document.getElementById("slotBudget").textContent = state.budget ? `₹${state.budget.toLocaleString()}` : "Not specified";
  document.getElementById("slotTravelers").textContent = `${state.travelers || 1} Traveler${(state.travelers || 1) > 1 ? 's' : ''}`;

  if (document.getElementById("slotTravelWith")) {
    document.getElementById("slotTravelWith").textContent = state.travel_with || "Not specified";
  }
  if (document.getElementById("slotTransport")) {
    document.getElementById("slotTransport").textContent = state.transport || "Not specified";
  }
  if (document.getElementById("slotAccommodation")) {
    document.getElementById("slotAccommodation").textContent = state.accommodation || "Not specified";
  }

  const interestsContainer = document.getElementById("slotInterests");
  const interests = state.interests || [];
  if (interests.length > 0) {
    interestsContainer.innerHTML = interests.map(i => `<span class="interest-tag">${i}</span>`).join('');
  } else {
    interestsContainer.innerHTML = '<span class="tag-empty">None specified</span>';
  }

  const excludedContainer = document.getElementById("excludedContainer");
  const excluded = state.excluded_categories || [];
  if (excluded.length > 0) {
    excludedContainer.style.display = "flex";
    document.getElementById("slotExcluded").innerHTML = excluded.map(e => `<span class="excluded-tag">${e}</span>`).join('');
  } else {
    excludedContainer.style.display = "none";
  }
}

function updateNlpInspectorUI(trace) {
  const intentElem = document.getElementById("nlpIntent");
  const confElem = document.getElementById("nlpConf");
  const barElem = document.getElementById("nlpConfBar");

  const confPercent = Math.round((trace.confidence || 0) * 100);
  intentElem.textContent = trace.intent || "Unknown";

  if (trace.dialogue_state && document.getElementById("slotStage")) {
    document.getElementById("slotStage").textContent = trace.dialogue_state.current_stage || "Collecting Details";
  }
  confElem.textContent = `${confPercent}%`;
  barElem.style.width = `${confPercent}%`;

  const topList = document.getElementById("nlpTopIntents");
  if (trace.top_predictions && trace.top_predictions.length > 0) {
    topList.innerHTML = trace.top_predictions.map(p => `
      <div class="intent-row">
        <span>${p.intent}</span>
        <span>${Math.round(p.confidence * 100)}%</span>
      </div>
    `).join('');
  }

  document.getElementById("nlpTokenCount").textContent = `${trace.token_count || 0} tokens`;
  const cleanTokensDiv = document.getElementById("nlpCleanTokens");
  const tokens = trace.filtered_tokens || trace.tokens || [];
  if (tokens.length > 0) {
    cleanTokensDiv.innerHTML = tokens.map(t => `<span class="token-pill">${t}</span>`).join('');
  } else {
    cleanTokensDiv.innerHTML = '<span class="token-empty">None</span>';
  }

  const stopDiv = document.getElementById("nlpStopwords");
  const stopwords = trace.stopwords_removed || [];
  if (stopwords.length > 0) {
    stopDiv.innerHTML = stopwords.map(s => `<span class="token-pill stopword">${s}</span>`).join('');
  } else {
    stopDiv.innerHTML = '<span class="token-empty">None filtered</span>';
  }

  const tfidfDiv = document.getElementById("nlpTfidf");
  const tfidf = trace.top_tfidf_features || [];
  if (tfidf.length > 0) {
    tfidfDiv.innerHTML = tfidf.map(f => {
      const pct = Math.min(100, Math.round(f.weight * 100));
      return `
        <div class="tfidf-item">
          <span class="tfidf-word" title="${f.term}">${f.term}</span>
          <div class="tfidf-track">
            <div class="tfidf-fill" style="width: ${pct}%;"></div>
          </div>
          <span class="tfidf-score">${f.weight}</span>
        </div>
      `;
    }).join('');
  } else {
    tfidfDiv.innerHTML = '<span class="token-empty">No active TF-IDF weights</span>';
  }

  document.getElementById("nlpJson").textContent = JSON.stringify(trace.extracted_entities || {}, null, 2);
}

function saveToChatHistory(queryText) {
  if (!chatHistory.includes(queryText)) {
    chatHistory.unshift(queryText);
    if (chatHistory.length > 15) chatHistory.pop();
    localStorage.setItem("tripwise_history", JSON.stringify(chatHistory));
    renderChatHistory();
  }
}

function renderChatHistory(filter = "") {
  const container = document.getElementById("chatHistoryList");
  const badge = document.getElementById("chatCountBadge");
  const filtered = chatHistory.filter(q => q.toLowerCase().includes(filter.toLowerCase()));

  badge.textContent = filtered.length;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="history-empty-state">
        <div class="empty-icon-circle">
          <i class="fa-regular fa-comment-dots"></i>
          <span class="purple-dot"></span>
        </div>
        <p class="empty-text">No Chat History</p>
        <button class="btn-new-chat-outline" onclick="startNewChat()">
          <i class="fa-solid fa-plus"></i> New Chat
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => `
    <button class="history-item-btn" onclick="triggerPrompt('${escapeAttr(item)}')">
      ${escapeHtml(item)}
    </button>
  `).join('');
}

function filterChatHistory(query) {
  renderChatHistory(query);
}

function switchChatListTab(tab) {
  document.getElementById("tabAllChats").classList.toggle("active", tab === 'all');
  document.getElementById("tabTrips").classList.toggle("active", tab === 'trips');
  if (tab === 'trips') {
    renderChatHistory("trip");
  } else {
    renderChatHistory("");
  }
}

async function startNewChat() {
  sessionId = "sess_" + Math.random().toString(36).substring(2, 9);
  localStorage.setItem("tripwise_session_id", sessionId);

  await fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId })
  });

  currentItineraryData = null;
  currentBookingData = null;
  document.getElementById("chatSessionTitle").textContent = "New Chat";
  document.getElementById("messagesContainer").innerHTML = "";
  document.getElementById("welcomeHero").style.display = "flex";
  document.getElementById("userInput").value = "";
  document.getElementById("userInput").focus();
}

function showTyping(show) {
  document.getElementById("typingIndicator").style.display = show ? "flex" : "none";
  scrollToBottom();
}

function scrollToBottom() {
  const stream = document.getElementById("chatStream");
  stream.scrollTop = stream.scrollHeight;
}

function exportItinerary() {
  downloadInvoiceDirect();
}

// ==========================================================================
// BACKGROUND THEME CONTROLLER
// ==========================================================================
const THEME_NAMES = {
  sunrise: "Sunrise Aura",
  mountain: "Mountain Mist",
  sunset: "Golden Sunset",
  wallpaper: "Scenic Wallpaper",
  dark: "Dark Luxe",
  minimal: "Pure Minimal"
};

function initTheme() {
  const savedTheme = localStorage.getItem("tripwise_bg_theme") || "sunrise";
  applyTheme(savedTheme);
}

function toggleThemeMenu(event) {
  if (event) event.stopPropagation();
  const menu = document.getElementById("themeDropdownMenu");
  if (menu) {
    menu.classList.toggle("show");
  }
}

function selectTheme(themeKey) {
  applyTheme(themeKey);
  localStorage.setItem("tripwise_bg_theme", themeKey);
  const menu = document.getElementById("themeDropdownMenu");
  if (menu) menu.classList.remove("show");
}

function applyTheme(themeKey) {
  document.body.classList.remove("theme-sunrise", "theme-mountain", "theme-sunset", "theme-wallpaper", "theme-dark", "theme-minimal");
  document.body.classList.add(`theme-${themeKey}`);
  
  const label = document.getElementById("currentThemeName");
  if (label && THEME_NAMES[themeKey]) {
    label.textContent = THEME_NAMES[themeKey];
  }

  // Update active state in menu
  document.querySelectorAll(".theme-option").forEach(opt => {
    opt.classList.toggle("active", opt.getAttribute("onclick")?.includes(`'${themeKey}'`));
  });
}

// Close theme menu when clicking outside
document.addEventListener("click", (e) => {
  const container = document.querySelector(".theme-menu-container");
  if (container && !container.contains(e.target)) {
    const menu = document.getElementById("themeDropdownMenu");
    if (menu) menu.classList.remove("show");
  }
});

// Run theme init immediately
initTheme();
document.addEventListener("DOMContentLoaded", initTheme);

function formatMarkdown(text) {
  if (!text) return "";

  // Split lines to detect markdown tables
  const lines = text.split("\n");
  let inTable = false;
  let tableRows = [];
  let processedLines = [];

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      inTable = true;
      tableRows.push(trimmed);
    } else {
      if (inTable) {
        processedLines.push(renderMarkdownTableHtml(tableRows));
        tableRows = [];
        inTable = false;
      }
      processedLines.push(rawLine);
    }
  }
  if (inTable && tableRows.length > 0) {
    processedLines.push(renderMarkdownTableHtml(tableRows));
  }

  let html = processedLines.join("\n");
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`([^`]+)`/g, '<code style="background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.85em; color: #0f172a;">$1</code>');
  html = html.replace(/^### (.*$)/gim, '<h4 style="font-size: 0.95rem; margin: 8px 0 4px; color: #0f172a;">$1</h4>');
  html = html.replace(/^> (.*$)/gim, '<blockquote class="chat-quote">$1</blockquote>');
  html = html.replace(/^[•\-] (.*$)/gim, '<li style="margin-left: 18px; margin-bottom: 3px;">$1</li>');
  html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
  return html;
}

function renderMarkdownTableHtml(rows) {
  if (rows.length < 2) return rows.join("<br>");
  const parseRow = (r) => r.split("|").slice(1, -1).map(c => c.trim());
  const headerCells = parseRow(rows[0]);
  
  const dataRows = [];
  for (let i = 1; i < rows.length; i++) {
    const cells = parseRow(rows[i]);
    if (cells.every(c => /^:?-+:?$/.test(c))) continue; // separator row
    dataRows.push(cells);
  }

  const thHtml = headerCells.map(h => `<th style="background: rgba(99, 102, 241, 0.08); padding: 8px 12px; border: 1px solid #cbd5e1; font-weight: 700; text-align: left; color: #1e293b; font-size: 0.86rem;">${h}</th>`).join("");
  const trHtml = dataRows.map((row, idx) => {
    const bg = idx % 2 === 0 ? '#ffffff' : '#f8fafc';
    const tds = row.map(c => {
      let formattedCell = c.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      return `<td style="padding: 9px 12px; border: 1px solid #e2e8f0; font-size: 0.86rem; color: #334155; line-height: 1.45;">${formattedCell}</td>`;
    }).join("");
    return `<tr style="background: ${bg};">${tds}</tr>`;
  }).join("");

  return `<div style="overflow-x: auto; margin: 12px 0;"><table style="width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
    <thead><tr>${thHtml}</tr></thead>
    <tbody>${trHtml}</tbody>
  </table></div>`;
}

function escapeHtml(string) {
  const entityMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return String(string).replace(/[&<>"']/g, s => entityMap[s]);
}

function escapeAttr(string) {
  return String(string).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
