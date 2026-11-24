const state = {
  products: [],
  categories: [],
  rarities: [],
  cart: readStorage("brainrot-cart", {}),
  orders: [],
  user: null,
  csrfToken: "",
  authMode: "login",
  view: "catalog",
};

const money = cents => (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[char]));

function readStorage(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    return value ?? fallback;
  } catch {
    return fallback;
  }
}

function saveStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const method = (options.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && state.csrfToken) {
    headers.set("X-CSRF-Token", state.csrfToken);
  }
  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  let result = {};
  if (text) {
    try {
      result = JSON.parse(text);
    } catch {
      throw new Error("O servidor retornou uma resposta inválida.");
    }
  }
  if (!response.ok) throw new Error(result.error || "Não foi possível concluir a operação.");
  return result;
}

function setView(view) {
  if (view === "admin" && state.user?.role !== "admin") view = "catalog";
  if (view === "orders" && !state.user) view = "account";
  state.view = view;
  document.querySelectorAll(".view").forEach(section => section.classList.add("hidden"));
  document.getElementById(`${view}-view`).classList.remove("hidden");
  document.querySelectorAll(".nav-button").forEach(button => button.classList.toggle("active", button.dataset.view === view));
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (view === "cart") renderCart();
  if (view === "orders") loadOrders();
}

function updateCartCount() {
  const count = Object.values(state.cart).reduce((sum, quantity) => sum + quantity, 0);
  document.getElementById("cart-count").textContent = count;
}

function card(product) {
  return `<article class="product-card" data-product="${escapeHtml(product.slug)}" tabindex="0" role="button" aria-label="Ver ${escapeHtml(product.name)}">
    <div class="card-image"><img src="${escapeHtml(product.image_path)}" alt="${escapeHtml(product.name)}" loading="lazy"><span class="rarity" style="background:${escapeHtml(product.rarity_color)}">${escapeHtml(product.rarity)}</span></div>
    <div class="card-copy"><h3>${escapeHtml(product.name)}</h3><span class="card-category">${escapeHtml(product.category)}</span>
      <div class="card-bottom"><span class="price">${money(product.price_cents)}</span><span class="stock">${product.stock ? `${product.stock} disponíveis` : "Esgotado"}</span></div>
    </div>
  </article>`;
}

function renderCatalog() {
  const query = document.getElementById("search").value.trim().toLocaleLowerCase("pt-BR");
  const rarity = document.getElementById("rarity-filter").value;
  const products = state.products.filter(product => {
    const searchable = `${product.name} ${product.description} ${product.category} ${product.rarity}`.toLocaleLowerCase("pt-BR");
    return (!query || searchable.includes(query)) && (!rarity || product.rarity === rarity);
  });
  const grid = document.getElementById("catalog-grid");
  document.getElementById("catalog-count").textContent = `${products.length} personagens para descobrir`;
  grid.innerHTML = products.length ? products.map(card).join("") : '<p class="message">Nenhum personagem encontrado com esses filtros.</p>';
  grid.querySelectorAll(".product-card").forEach(element => {
    const open = () => showDetail(element.dataset.product);
    element.addEventListener("click", open);
    element.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); }
    });
  });
}

async function showDetail(slug) {
  try {
    const product = await request(`/api/brainrots/${encodeURIComponent(slug)}`);
    document.getElementById("detail-content").innerHTML = `<div class="detail-panel">
      <div class="detail-image"><img src="${escapeHtml(product.image_path)}" alt="${escapeHtml(product.name)}"></div>
      <div class="detail-copy"><span class="rarity" style="position:static;background:${escapeHtml(product.rarity_color)}">${escapeHtml(product.rarity)}</span>
        <h1>${escapeHtml(product.name)}</h1><p>${escapeHtml(product.description)}</p><p class="card-category">${escapeHtml(product.category)}</p>
        <div class="price">${money(product.price_cents)}</div><p class="detail-stock">${product.stock ? `${product.stock} unidades em estoque` : "Produto esgotado"}</p>
        <button class="primary-button" id="add-to-cart" ${product.stock ? "" : "disabled"}>Adicionar ao carrinho</button>
      </div></div>`;
    document.getElementById("add-to-cart").addEventListener("click", () => addToCart(product));
    setView("detail");
  } catch (error) {
    showError(error.message);
  }
}

function addToCart(product) {
  const current = state.cart[product.slug] || 0;
  if (current >= product.stock) {
    showError(`Estoque máximo de ${product.name} já está no carrinho.`);
    return;
  }
  state.cart[product.slug] = current + 1;
  saveStorage("brainrot-cart", state.cart);
  updateCartCount();
  setView("cart");
}

function cartRows() {
  return Object.entries(state.cart).map(([slug, quantity]) => {
    const product = state.products.find(item => item.slug === slug);
    return product ? { product, quantity } : null;
  }).filter(Boolean);
}

function renderCart() {
  const content = document.getElementById("cart-content");
  const rows = cartRows();
  if (!rows.length) {
    content.innerHTML = '<div class="empty-state"><strong>Seu carrinho está descansando.</strong>Encontre um personagem para começar a coleção.<br><button class="primary-button" data-view="catalog">Explorar a loja</button></div>';
    content.querySelector("[data-view]").addEventListener("click", () => setView("catalog"));
    return;
  }
  const total = rows.reduce((sum, row) => sum + row.product.price_cents * row.quantity, 0);
  content.innerHTML = `<div class="cart-list">${rows.map(({ product, quantity }) => `
    <div class="cart-row"><img src="${escapeHtml(product.image_path)}" alt="${escapeHtml(product.name)}">
      <div class="cart-info"><strong>${escapeHtml(product.name)}</strong><small>${money(product.price_cents)} cada · ${escapeHtml(product.rarity)}</small></div>
      <div class="quantity-controls"><button data-action="decrease" data-slug="${escapeHtml(product.slug)}" aria-label="Diminuir quantidade">−</button><span>${quantity}</span><button data-action="increase" data-slug="${escapeHtml(product.slug)}" aria-label="Aumentar quantidade">+</button></div>
      <strong>${money(product.price_cents * quantity)}</strong><button class="remove-button" data-action="remove" data-slug="${escapeHtml(product.slug)}" aria-label="Remover ${escapeHtml(product.name)}">×</button>
    </div>`).join("")}</div>
    <div class="cart-summary"><div class="summary-line"><span>Total</span><span>${money(total)}</span></div><button id="checkout" class="primary-button">Finalizar compra simulada</button></div>`;
  content.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => changeCart(button.dataset.slug, button.dataset.action)));
  document.getElementById("checkout").addEventListener("click", checkout);
}

function changeCart(slug, action) {
  if (action === "remove" || (action === "decrease" && state.cart[slug] <= 1)) delete state.cart[slug];
  else if (action === "decrease") state.cart[slug] -= 1;
  else {
    const product = state.products.find(item => item.slug === slug);
    if (product && state.cart[slug] < product.stock) state.cart[slug] += 1;
    else showError("Não há mais unidades disponíveis em estoque.");
  }
  saveStorage("brainrot-cart", state.cart);
  updateCartCount();
  renderCart();
}

async function checkout() {
  if (!state.user) {
    showError("Entre ou crie uma conta para finalizar a compra.");
    setView("account");
    return;
  }
  const button = document.getElementById("checkout");
  button.disabled = true;
  button.textContent = "Processando...";
  try {
    await request("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: Object.entries(state.cart).map(([slug, quantity]) => ({ slug, quantity })) }),
    });
    state.cart = {};
    saveStorage("brainrot-cart", state.cart);
    state.products = await request("/api/brainrots");
    renderCatalog();
    updateCartCount();
    setView("orders");
  } catch (error) {
    button.disabled = false;
    button.textContent = "Finalizar compra simulada";
    showError(error.message);
  }
}

async function loadOrders() {
  const target = document.getElementById("orders-content");
  target.innerHTML = '<p class="message">Carregando pedidos...</p>';
  try {
    state.orders = await request("/api/orders");
    renderOrders();
  } catch (error) {
    target.innerHTML = `<p class="message error">${escapeHtml(error.message)}</p>`;
  }
}

function renderOrders() {
  const target = document.getElementById("orders-content");
  if (!state.orders.length) {
    target.innerHTML = '<div class="empty-state"><strong>Nenhum pedido por enquanto.</strong>Quando encontrar seu brainrot, ele aparecerá aqui.</div>';
    return;
  }
  target.innerHTML = `<div class="orders-list">${state.orders.map(order => `<article class="order-card">
    <div class="order-meta"><span>Pedido #${order.id}</span><span>${new Date(order.created_at).toLocaleDateString("pt-BR")} · ${money(order.total_cents)}</span></div>
    <div class="order-items">${order.items.map(item => `<div class="order-item"><img src="${escapeHtml(item.image_path)}" alt="${escapeHtml(item.name)}"><span>${escapeHtml(item.name)}<br><small>${item.quantity} × ${money(item.price_cents)}</small></span></div>`).join("")}</div>
  </article>`).join("")}</div>`;
}

function renderAccount() {
  const loggedIn = Boolean(state.user);
  document.getElementById("auth-panel").classList.toggle("hidden", loggedIn);
  document.getElementById("logged-in-panel").classList.toggle("hidden", !loggedIn);
  document.getElementById("orders-nav").classList.toggle("hidden", !loggedIn);
  document.getElementById("admin-nav").classList.toggle("hidden", state.user?.role !== "admin");
  document.getElementById("account-admin-button").classList.toggle("hidden", state.user?.role !== "admin");
  document.getElementById("account-nav").textContent = loggedIn ? state.user.username : "Entrar";
  document.getElementById("account-title").textContent = loggedIn ? "Sua conta" : "Entre ou crie sua conta";
  if (loggedIn) {
    document.getElementById("account-welcome").textContent = `Você está conectado como ${state.user.username}${state.user.role === "admin" ? " (administrador)" : ""}.`;
  }
}

function showAuthError(message) {
  const target = document.getElementById("auth-error");
  target.textContent = message;
  target.classList.remove("hidden");
}

function setAuthMode(mode) {
  state.authMode = mode;
  document.querySelectorAll("[data-auth-mode]").forEach(button => button.classList.toggle("selected", button.dataset.authMode === mode));
  document.querySelector("#auth-form button[type=submit]").textContent = mode === "login" ? "Entrar" : "Criar conta";
  document.querySelector("#auth-form [name=password]").autocomplete = mode === "login" ? "current-password" : "new-password";
  document.getElementById("auth-error").classList.add("hidden");
}

function populateSelect(target, values, placeholder) {
  target.innerHTML = `<option value="">${placeholder}</option>${values.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("")}`;
}

function populateRarityFilter(rarities) {
  const filter = document.getElementById("rarity-filter");
  filter.innerHTML = `<option value="">Todas</option>${rarities.map(item => `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`).join("")}`;
}

async function authenticate(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const endpoint = state.authMode === "login" ? "/api/auth/login" : "/api/auth/register";
  const submit = event.currentTarget.querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const result = await request(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password"),
      }),
    });
    state.user = result.user;
    state.csrfToken = result.csrf_token;
    renderAccount();
    event.currentTarget.reset();
    await loadOrders();
    setView("catalog");
    showError(state.authMode === "login" ? "Login realizado com sucesso." : "Conta criada com sucesso.");
  } catch (error) {
    showAuthError(error.message);
  } finally {
    submit.disabled = false;
  }
}

async function logout() {
  try {
    const result = await request("/api/auth/logout", { method: "POST" });
    state.user = null;
    state.csrfToken = result.csrf_token;
    state.orders = [];
    renderAccount();
    setView("catalog");
  } catch (error) {
    showError(error.message);
  }
}

async function createBrainrot(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector("button[type=submit]");
  const message = document.getElementById("admin-message");
  submit.disabled = true;
  message.classList.add("hidden");
  try {
    const product = await request("/api/brainrots", {
      method: "POST",
      body: new FormData(form),
    });
    state.products = await request("/api/brainrots");
    renderCatalog();
    form.reset();
    populateSelect(document.getElementById("admin-category"), state.categories, "Selecione");
    populateSelect(document.getElementById("admin-rarity"), state.rarities, "Selecione");
    message.textContent = `${product.name} foi adicionado ao catálogo.`;
    message.classList.remove("hidden");
    message.classList.add("success");
  } catch (error) {
    message.textContent = error.message;
    message.classList.remove("hidden", "success");
  } finally {
    submit.disabled = false;
  }
}

function showError(message) {
  const target = document.getElementById("toast");
  target.textContent = message;
  target.classList.remove("hidden");
  window.setTimeout(() => target.classList.add("hidden"), 4500);
}

document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
document.getElementById("search").addEventListener("input", renderCatalog);
document.getElementById("rarity-filter").addEventListener("change", renderCatalog);
document.querySelectorAll("[data-auth-mode]").forEach(button => button.addEventListener("click", () => setAuthMode(button.dataset.authMode)));
document.getElementById("auth-form").addEventListener("submit", authenticate);
document.getElementById("logout-button").addEventListener("click", logout);
document.getElementById("admin-form").addEventListener("submit", createBrainrot);

async function initialize() {
  const [auth, products, options] = await Promise.all([
    request("/api/auth/me"),
    request("/api/brainrots"),
    request("/api/catalog-options"),
  ]);
  state.user = auth.user;
  state.csrfToken = auth.csrf_token;
  state.products = products;
  state.categories = options.categories;
  state.rarities = options.rarities;
  populateRarityFilter(state.rarities);
  populateSelect(document.getElementById("admin-category"), state.categories, "Selecione");
  populateSelect(document.getElementById("admin-rarity"), state.rarities, "Selecione");
  renderCatalog();
  renderAccount();
  updateCartCount();
}

initialize().catch(error => {
  document.getElementById("catalog-count").textContent = "Não foi possível carregar o catálogo.";
  showError(error.message);
});