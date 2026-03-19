const state = {
  recommendations: [],
  history: [],
  profile: null,
  ai: null,
  selected: null,
  currentMood: "ocupado",
};

const els = {
  profileForm: document.querySelector("#profile-form"),
  contextForm: document.querySelector("#context-form"),
  recommendations: document.querySelector("#recommendations"),
  detailPanel: document.querySelector("#detail-panel"),
  historyList: document.querySelector("#history-list"),
  statusText: document.querySelector("#status-text"),
  cardTemplate: document.querySelector("#card-template"),
  aiSummary: document.querySelector("#ai-summary"),
  aiRecipeTip: document.querySelector("#ai-recipe-tip"),
  aiShoppingTip: document.querySelector("#ai-shopping-tip"),
};

const parseCommaList = (value) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const currencyLevel = (level) => "€".repeat(Number(level));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Error de servidor");
  }

  return payload;
}

function fillProfile(profile) {
  state.profile = profile;
  els.profileForm.name.value = profile.name;
  els.profileForm.goal.value = profile.goal;
  els.profileForm.favorite_cuisines.value = profile.favorite_cuisines.join(", ");
  els.profileForm.favorite_ingredients.value = profile.favorite_ingredients.join(", ");
  els.profileForm.allergies.value = profile.allergies.join(", ");
  els.profileForm.disliked_ingredients.value = profile.disliked_ingredients.join(", ");
  els.profileForm.weeknight_minutes.value = profile.weeknight_minutes;
  els.profileForm.budget_level.value = String(profile.budget_level);

  for (const checkbox of els.profileForm.querySelectorAll('input[name="preferred_modes"]')) {
    checkbox.checked = profile.preferred_modes.includes(checkbox.value);
  }

  els.contextForm.time_available.value = profile.weeknight_minutes;
}

function renderAI(ai) {
  state.ai = ai;
  els.aiSummary.textContent = ai?.summary || "Sin resumen disponible.";
  els.aiRecipeTip.textContent = ai?.recipe_tip || "-";
  els.aiShoppingTip.textContent = ai?.shopping_tip || "-";
}

function renderHistory() {
  els.historyList.innerHTML = "";

  for (const item of state.history) {
    const li = document.createElement("li");
    const when = new Date(item.created_at).toLocaleString("es-ES", {
      dateStyle: "short",
      timeStyle: "short",
    });
    li.textContent = `${item.dish_name} · ${item.action} · ${item.mood || "sin contexto"} · ${when}`;
    els.historyList.append(li);
  }
}

function selectRecommendation(name) {
  const recommendation = state.recommendations.find((item) => item.name === name);
  if (!recommendation) return;
  state.selected = recommendation;

  const ingredients = recommendation.shopping_list.length
    ? `<ul class="detail-list">${recommendation.shopping_list
        .map(
          (item) => `<li>${item.ingredient} — ${item.quantity} <strong>(${item.suggested_store})</strong></li>`,
        )
        .join("")}</ul>`
    : `<p class="muted">Al ser delivery, no necesitas lista de compra.</p>`;

  const steps = recommendation.steps.length
    ? `<ol class="detail-list">${recommendation.steps.map((step) => `<li>${step}</li>`).join("")}</ol>`
    : `<p class="muted">Abre la app de delivery o integra restaurantes reales en la siguiente iteración.</p>`;

  const penalties = recommendation.penalties.length
    ? `<ul class="detail-list">${recommendation.penalties.map((item) => `<li>${item}</li>`).join("")}</ul>`
    : `<p class="muted">No detectamos fricciones importantes para esta opción.</p>`;

  els.detailPanel.innerHTML = `
    <p class="eyebrow">Detalle</p>
    <div class="section-heading">
      <div>
        <h2>${recommendation.name}</h2>
        <p class="muted">${recommendation.description}</p>
      </div>
      <span class="badge ${recommendation.mode}">${recommendation.mode === "cook" ? "Cocinar" : "Delivery"}</span>
    </div>
    <p><strong>Cocina:</strong> ${recommendation.cuisine} · <strong>Tiempo:</strong> ${recommendation.cook_time} min · <strong>Presupuesto:</strong> ${currencyLevel(recommendation.price_level)}</p>
    <div>
      <h3>Por qué te lo recomendamos</h3>
      <ul class="detail-list">${recommendation.reasons.map((item) => `<li>${item}</li>`).join("")}</ul>
    </div>
    <div>
      <h3>Posibles fricciones</h3>
      ${penalties}
    </div>
    <div>
      <h3>Lista exacta de compra</h3>
      ${ingredients}
    </div>
    <div>
      <h3>Paso a paso</h3>
      ${steps}
    </div>
    <div class="detail-actions">
      <button class="js-record" data-action="liked" data-dish="${recommendation.name}">Me gusta</button>
      <button class="secondary js-record" data-action="saved" data-dish="${recommendation.name}">Guardar</button>
      <button class="ghost js-record" data-action="dismissed" data-dish="${recommendation.name}">No se me antoja</button>
    </div>
    <div class="notice">Tip AI: ${state.ai?.recipe_tip || "La app puede personalizar aún más esta receta si configuras tu clave de OpenAI."}</div>
  `;

  for (const button of els.detailPanel.querySelectorAll(".js-record")) {
    button.addEventListener("click", () => recordInteraction(button.dataset.dish, button.dataset.action));
  }
}

function renderRecommendations() {
  els.recommendations.innerHTML = "";
  if (!state.recommendations.length) {
    els.recommendations.innerHTML = `<p class="muted">No encontramos recomendaciones para este contexto.</p>`;
    return;
  }

  for (const recommendation of state.recommendations) {
    const node = els.cardTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".mode").textContent = recommendation.mode === "cook" ? "Cocinar" : "Delivery";
    node.querySelector(".mode").classList.add(recommendation.mode);
    node.querySelector(".score").textContent = `Score ${recommendation.score}`;
    node.querySelector(".title").textContent = recommendation.name;
    node.querySelector(".description").textContent = recommendation.description;
    node.querySelector(
      ".meta",
    ).textContent = `${recommendation.cuisine} · ${recommendation.cook_time} min · presupuesto ${currencyLevel(recommendation.price_level)}`;
    node.querySelector(".reasons").innerHTML = recommendation.reasons.map((item) => `<li>${item}</li>`).join("");
    node.querySelector(".view-detail").addEventListener("click", () => selectRecommendation(recommendation.name));
    node.querySelector(".quick-like").addEventListener("click", () => recordInteraction(recommendation.name, "liked"));
    els.recommendations.append(node);
  }

  selectRecommendation(state.recommendations[0].name);
}

async function recordInteraction(dishName, action) {
  try {
    const response = await api("/api/interactions", {
      method: "POST",
      body: JSON.stringify({ dish_name: dishName, action, mood: state.currentMood }),
    });
    state.history = response.history;
    renderHistory();
    els.statusText.textContent = `Registrado: ${action} en ${dishName}`;
  } catch (error) {
    els.statusText.textContent = error.message;
  }
}

async function refreshRecommendations(payload) {
  els.statusText.textContent = "Pensando recomendaciones...";
  try {
    const response = await api("/api/recommendations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.recommendations = response.recommendations;
    state.currentMood = payload.mood;
    renderAI(response.ai);
    renderRecommendations();
    els.statusText.textContent = "Recomendaciones actualizadas.";
  } catch (error) {
    els.statusText.textContent = error.message;
  }
}

els.profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    name: els.profileForm.name.value,
    goal: els.profileForm.goal.value,
    favorite_cuisines: parseCommaList(els.profileForm.favorite_cuisines.value),
    favorite_ingredients: parseCommaList(els.profileForm.favorite_ingredients.value),
    allergies: parseCommaList(els.profileForm.allergies.value),
    disliked_ingredients: parseCommaList(els.profileForm.disliked_ingredients.value),
    weeknight_minutes: Number(els.profileForm.weeknight_minutes.value),
    budget_level: Number(els.profileForm.budget_level.value),
    preferred_modes: [...els.profileForm.querySelectorAll('input[name="preferred_modes"]:checked')].map(
      (checkbox) => checkbox.value,
    ),
  };

  try {
    const response = await api("/api/profile", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    fillProfile(response.profile);
    els.statusText.textContent = "Perfil guardado.";
    await refreshRecommendations({
      mode: els.contextForm.mode.value,
      mood: els.contextForm.mood.value,
      time_available: Number(els.contextForm.time_available.value),
      supermarket: els.contextForm.supermarket.value,
      wants_variety: els.contextForm.wants_variety.checked,
    });
  } catch (error) {
    els.statusText.textContent = error.message;
  }
});

els.contextForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await refreshRecommendations({
    mode: els.contextForm.mode.value,
    mood: els.contextForm.mood.value,
    time_available: Number(els.contextForm.time_available.value),
    supermarket: els.contextForm.supermarket.value,
    wants_variety: els.contextForm.wants_variety.checked,
  });
});

async function bootstrap() {
  try {
    const payload = await api("/api/bootstrap");
    fillProfile(payload.profile);
    state.history = payload.history;
    state.recommendations = payload.recommendations;
    renderHistory();
    renderAI(payload.ai);
    renderRecommendations();
    els.statusText.textContent = "Listo para decidir tu próxima comida.";
  } catch (error) {
    els.statusText.textContent = error.message;
  }
}

bootstrap();
