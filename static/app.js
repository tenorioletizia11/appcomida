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
  heroTitle: document.querySelector("#hero-title"),
  recipeHeroTitle: document.querySelector("#recipe-hero-title"),
  recipeTitle: document.querySelector("#recipe-title"),
  recipeSteps: document.querySelector("#recipe-steps"),
  shoppingPreview: document.querySelector("#shopping-preview"),
  screens: [...document.querySelectorAll(".screen")],
  navItems: [...document.querySelectorAll(".nav-item")],
  goProfile: document.querySelector("#go-profile"),
  goRecipes: document.querySelector("#go-recipes"),
  goToday: document.querySelector("#go-today"),
};

const parseCommaList = (value) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const currencyLevel = (level) => "€".repeat(Number(level));
const modeLabel = (mode) => (mode === "cook" ? "Cocinar" : "Delivery");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Error de servidor");
  return payload;
}

function setScreen(screen) {
  els.screens.forEach((section) => section.classList.toggle("active", section.dataset.screen === screen));
  els.navItems.forEach((item) => item.classList.toggle("active", item.dataset.target === screen));
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
  els.contextForm.time_available.value = profile.weeknight_minutes;

  for (const checkbox of els.profileForm.querySelectorAll('input[name="preferred_modes"]')) {
    checkbox.checked = profile.preferred_modes.includes(checkbox.value);
  }
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

function renderRecipePreview(recommendation) {
  els.recipeHeroTitle.textContent = recommendation
    ? `Receta favorita para ${recommendation.name}`
    : "Cocina sin fricción";
  els.recipeTitle.textContent = recommendation ? recommendation.name : "Elige una receta";

  els.shoppingPreview.innerHTML = recommendation?.shopping_list?.length
    ? recommendation.shopping_list
        .map((item) => `<li>${item.ingredient} — ${item.quantity} <strong>(${item.suggested_store})</strong></li>`)
        .join("")
    : `<li>No necesitas compra extra para esta opción.</li>`;

  els.recipeSteps.innerHTML = recommendation?.steps?.length
    ? recommendation.steps.map((step) => `<li>${step}</li>`).join("")
    : `<li>Abre una app de delivery o conecta restaurantes reales en una siguiente iteración.</li>`;
}

function selectRecommendation(name, nextScreen = false) {
  const recommendation = state.recommendations.find((item) => item.name === name);
  if (!recommendation) return;

  state.selected = recommendation;
  renderRecipePreview(recommendation);

  const ingredients = recommendation.shopping_list.length
    ? `<ul class="detail-list">${recommendation.shopping_list
        .map(
          (item) => `<li>${item.ingredient} — ${item.quantity} <strong>(${item.suggested_store})</strong></li>`,
        )
        .join("")}</ul>`
    : `<p class="muted">Al ser delivery, no necesitas lista de compra.</p>`;

  const steps = recommendation.steps.length
    ? `<ol class="detail-list">${recommendation.steps.map((step) => `<li>${step}</li>`).join("")}</ol>`
    : `<p class="muted">Esta opción es ideal para pedir sin cocinar.</p>`;

  const penalties = recommendation.penalties.length
    ? `<ul class="detail-list">${recommendation.penalties.map((item) => `<li>${item}</li>`).join("")}</ul>`
    : `<p class="muted">No detectamos fricciones importantes para esta opción.</p>`;

  els.detailPanel.innerHTML = `
    <p class="eyebrow">Detalle elegido</p>
    <div class="section-header start">
      <div>
        <span class="badge ${recommendation.mode}">${modeLabel(recommendation.mode)}</span>
        <h2>${recommendation.name}</h2>
      </div>
      <span class="score-pill">Score ${recommendation.score}</span>
    </div>
    <p class="muted">${recommendation.description}</p>
    <p class="muted"><strong>${recommendation.cuisine}</strong> · ${recommendation.cook_time} min · presupuesto ${currencyLevel(recommendation.price_level)}</p>
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
    <div class="card-actions">
      <button class="js-record" data-action="liked" data-dish="${recommendation.name}">Me gusta</button>
      <button class="secondary js-open-recipes" type="button">Ir a receta</button>
    </div>
  `;

  els.detailPanel.querySelector(".js-record")?.addEventListener("click", () => recordInteraction(recommendation.name, "liked"));
  els.detailPanel.querySelector(".js-open-recipes")?.addEventListener("click", () => setScreen("recipes"));

  if (nextScreen) setScreen("recipes");
}

function renderRecommendations() {
  els.recommendations.innerHTML = "";
  if (!state.recommendations.length) {
    els.recommendations.innerHTML = `<p class="muted">No encontramos recomendaciones para este contexto.</p>`;
    renderRecipePreview(null);
    return;
  }

  for (const recommendation of state.recommendations) {
    const node = els.cardTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".mode").textContent = modeLabel(recommendation.mode);
    node.querySelector(".mode").classList.add(recommendation.mode);
    node.querySelector(".score-pill").textContent = `Score ${recommendation.score}`;
    node.querySelector(".title").textContent = recommendation.name;
    node.querySelector(".description").textContent = recommendation.description;
    node.querySelector(
      ".meta",
    ).textContent = `${recommendation.cuisine} · ${recommendation.cook_time} min · ${currencyLevel(recommendation.price_level)}`;
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
    els.statusText.textContent = `Guardado: ${action}`;
  } catch (error) {
    els.statusText.textContent = error.message;
  }
}

async function refreshRecommendations(payload) {
  els.statusText.textContent = "Pensando menú...";
  try {
    const response = await api("/api/recommendations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.recommendations = response.recommendations;
    state.currentMood = payload.mood;
    renderAI(response.ai);
    els.heroTitle.textContent = `Sugerencias para un día ${payload.mood}`;
    renderRecommendations();
    els.statusText.textContent = "Sugerencias listas";
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
    els.statusText.textContent = "Perfil actualizado";
    setScreen("today");
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

els.navItems.forEach((item) => item.addEventListener("click", () => setScreen(item.dataset.target)));
els.goProfile?.addEventListener("click", () => setScreen("profile"));
els.goRecipes?.addEventListener("click", () => {
  if (state.selected) selectRecommendation(state.selected.name, true);
  else setScreen("recipes");
});
els.goToday?.addEventListener("click", () => setScreen("today"));

async function bootstrap() {
  try {
    const payload = await api("/api/bootstrap");
    fillProfile(payload.profile);
    state.history = payload.history;
    state.recommendations = payload.recommendations;
    renderHistory();
    renderAI(payload.ai);
    renderRecommendations();
    els.statusText.textContent = "Listo para decidir";
  } catch (error) {
    els.statusText.textContent = error.message;
  }
}

bootstrap();
