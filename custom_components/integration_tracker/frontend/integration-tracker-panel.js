const STATUS_LABELS = {
  active: "Active",
  testing: "Testing",
  unused: "Unused",
  replace: "Replace",
  archived: "Archived",
};

const REVIEW_LABELS = {
  up_to_date: "Up to date",
  needs_review: "Needs review",
  never_reviewed: "Never reviewed",
};

const USAGE_TYPES = [
  "dashboard",
  "card",
  "automation",
  "script",
  "integration",
  "other",
];

const USAGE_ICONS = {
  dashboard: "mdi:view-dashboard",
  card: "mdi:card",
  automation: "mdi:robot",
  script: "mdi:script-text",
  integration: "mdi:puzzle",
  other: "mdi:link",
};

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const option = (value, label, selected) =>
  `<option value="${escapeHtml(value)}" ${selected === value ? "selected" : ""}>${escapeHtml(label)}</option>`;

class IntegrationTrackerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._loaded = false;
    this._loading = true;
    this._saving = false;
    this._error = "";
    this._data = undefined;
    this._selectedId = undefined;
    this._editingUsageId = undefined;
    this._filters = {
      query: "",
      installation: "all",
      status: "all",
      rating: "all",
      review: "all",
      source: "all",
      category: "all",
      tags: "",
      sort: "name",
      direction: "asc",
    };
  }

  set hass(value) {
    this._hass = value;
    if (!this._loaded && this.isConnected) {
      this._loaded = true;
      this.refresh();
    }
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    if (!this._bound) {
      this.shadowRoot.addEventListener("click", (event) => this._handleClick(event));
      this.shadowRoot.addEventListener("input", (event) => this._handleInput(event));
      this.shadowRoot.addEventListener("change", (event) => this._handleInput(event));
      this.shadowRoot.addEventListener("submit", (event) => this._handleSubmit(event));
      this._bound = true;
    }
    this.render();
    if (this._hass && !this._loaded) {
      this._loaded = true;
      this.refresh();
    }
  }

  async refresh() {
    if (!this._hass) return;
    this._loading = !this._data;
    this._error = "";
    this.render();
    try {
      this._data = await this._hass.callWS({ type: "integration_tracker/list" });
      if (this._selectedId && !this.selectedItem) this._selectedId = undefined;
    } catch (error) {
      this._error = error?.message || String(error);
    } finally {
      this._loading = false;
      this.render();
    }
  }

  get selectedItem() {
    return this._data?.items.find((item) => item.id === this._selectedId);
  }

  get filteredItems() {
    if (!this._data) return [];
    const query = this._filters.query.trim().toLocaleLowerCase();
    const wantedTags = this._filters.tags
      .split(",")
      .map((tag) => tag.trim().toLocaleLowerCase())
      .filter(Boolean);

    const items = this._data.items.filter((item) => {
      const searchable = [
        item.name,
        item.repository,
        item.notes,
        ...item.tags,
        ...item.usages.map((usage) => usage.name),
      ]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase();
      if (query && !searchable.includes(query)) return false;
      if (this._filters.installation === "installed" && !item.installed) return false;
      if (this._filters.installation === "uninstalled" && item.installed) return false;
      if (this._filters.status === "none" && item.status) return false;
      if (
        !["all", "none"].includes(this._filters.status) &&
        item.status !== this._filters.status
      ) return false;
      if (this._filters.rating === "none" && item.rating !== null) return false;
      if (
        !["all", "none"].includes(this._filters.rating) &&
        item.rating !== Number(this._filters.rating)
      ) return false;
      if (this._filters.review !== "all" && item.review_state !== this._filters.review) return false;
      if (this._filters.source !== "all" && item.source !== this._filters.source) return false;
      if (this._filters.category !== "all" && item.category !== this._filters.category) return false;
      const itemTags = item.tags.map((tag) => tag.toLocaleLowerCase());
      return wantedTags.every((tag) => itemTags.includes(tag));
    });

    const direction = this._filters.direction === "asc" ? 1 : -1;
    return items.sort((left, right) => {
      const leftValue = this._sortValue(left);
      const rightValue = this._sortValue(right);
      if (leftValue === rightValue) return left.name.localeCompare(right.name);
      if (leftValue === null || leftValue === undefined) return -1 * direction;
      if (rightValue === null || rightValue === undefined) return 1 * direction;
      return (leftValue < rightValue ? -1 : 1) * direction;
    });
  }

  _sortValue(item) {
    switch (this._filters.sort) {
      case "rating": return item.rating;
      case "status": return item.status || "";
      case "last_reviewed": return item.last_reviewed_at || "";
      case "discovered": return item.discovered_at;
      case "usages": return item.usages.length;
      case "installed": return item.installed ? 1 : 0;
      default: return item.name.toLocaleLowerCase();
    }
  }

  _handleInput(event) {
    const target = event.target;
    const filter = target.dataset?.filter;
    if (!filter) return;
    this._filters[filter] = target.value;
    this._renderResults();
  }

  async _handleClick(event) {
    const actionTarget = event.target.closest("[data-action]");
    if (!actionTarget) return;
    const action = actionTarget.dataset.action;
    if (action === "open") {
      this._selectedId = actionTarget.dataset.itemId;
      this._editingUsageId = undefined;
      this.render();
      queueMicrotask(() => this.shadowRoot.querySelector(".dialog")?.focus());
    } else if (action === "close") {
      this._selectedId = undefined;
      this._editingUsageId = undefined;
      this.render();
    } else if (action === "sync") {
      await this._sync(actionTarget);
    } else if (action === "review") {
      await this._review(actionTarget);
    } else if (action === "rating") {
      this._setRating(Number(actionTarget.dataset.rating));
    } else if (action === "clear-rating") {
      this._setRating(null);
    } else if (action === "edit-usage") {
      this._editingUsageId = actionTarget.dataset.usageId;
      this.render();
    } else if (action === "cancel-usage") {
      this._editingUsageId = undefined;
      this.render();
    } else if (action === "remove-usage") {
      await this._removeUsage(actionTarget);
    } else if (action === "usage-link") {
      this._openUrl(actionTarget.dataset.url);
    }
  }

  async _handleSubmit(event) {
    event.preventDefault();
    if (event.target.id === "details-form") await this._saveDetails(event.target);
    if (event.target.id === "usage-form") await this._saveUsage(event.target);
  }

  _setRating(value) {
    const input = this.shadowRoot.querySelector("#rating-value");
    if (!input) return;
    input.value = value ?? "";
    this.shadowRoot.querySelectorAll("[data-action='rating']").forEach((button) => {
      button.classList.toggle("selected", Number(button.dataset.rating) <= (value || 0));
      button.setAttribute("aria-pressed", Number(button.dataset.rating) === value ? "true" : "false");
    });
  }

  async _runMutation(button, request) {
    if (this._saving) return false;
    this._saving = true;
    this._error = "";
    if (button) button.disabled = true;
    try {
      await this._hass.callWS(request);
      await this.refresh();
      return true;
    } catch (error) {
      this._error = error?.message || String(error);
      this.render();
      return false;
    } finally {
      this._saving = false;
      if (button?.isConnected) button.disabled = false;
      this.render();
    }
  }

  async _sync(button) {
    const previousText = button.textContent;
    button.textContent = "Syncing…";
    const ok = await this._runMutation(button, { type: "integration_tracker/sync" });
    if (button.isConnected) button.textContent = previousText;
    if (ok) this._announce("Synchronization completed");
  }

  async _review(button) {
    const ok = await this._runMutation(button, {
      type: "integration_tracker/review",
      item_id: this._selectedId,
    });
    if (ok) this._announce("Review recorded");
  }

  async _saveDetails(form) {
    const submit = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const rating = formData.get("rating");
    const tags = formData
      .get("tags")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    const ok = await this._runMutation(submit, {
      type: "integration_tracker/update",
      item_id: this._selectedId,
      rating: rating ? Number(rating) : null,
      status: formData.get("status") || null,
      notes: formData.get("notes") || null,
      tags,
    });
    if (ok) this._announce("Details saved");
  }

  async _saveUsage(form) {
    const submit = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const request = {
      type: this._editingUsageId
        ? "integration_tracker/usage/update"
        : "integration_tracker/usage/add",
      item_id: this._selectedId,
      name: formData.get("usage-name"),
      usage_type: formData.get("usage-type"),
      url: formData.get("usage-url") || null,
    };
    if (this._editingUsageId) request.usage_id = this._editingUsageId;
    const ok = await this._runMutation(submit, request);
    if (ok) {
      this._editingUsageId = undefined;
      this.render();
      this._announce("Usage saved");
    }
  }

  async _removeUsage(button) {
    const ok = await this._runMutation(button, {
      type: "integration_tracker/usage/remove",
      item_id: this._selectedId,
      usage_id: button.dataset.usageId,
    });
    if (ok) this._announce("Usage removed");
  }

  _openUrl(url) {
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  _announce(message) {
    const live = this.shadowRoot.querySelector("#live-region");
    if (live) live.textContent = message;
  }

  render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <main>
        ${this._renderHeader()}
        <div id="live-region" class="sr-only" aria-live="polite"></div>
        ${this._error ? `<div class="message error" role="alert">${escapeHtml(this._error)}</div>` : ""}
        ${this._loading ? this._renderLoading() : this._renderContent()}
      </main>
      ${this.selectedItem ? this._renderDialog(this.selectedItem) : ""}
    `;
  }

  _renderHeader() {
    const lastSync = this._data?.last_synced_at
      ? this._formatDate(this._data.last_synced_at)
      : "Never";
    return `
      <header>
        <div>
          <h1>Integration Tracker</h1>
          <p>Inventory, context, lifecycle, and review for HACS repositories.</p>
        </div>
        <div class="sync-block">
          <span>Last synchronized: ${escapeHtml(lastSync)}</span>
          <button class="primary" data-action="sync" ${this._saving ? "disabled" : ""}>Sync now</button>
        </div>
      </header>
      ${this._data?.sync_error ? `<div class="message warning">HACS sync: ${escapeHtml(this._data.sync_error)}</div>` : ""}
    `;
  }

  _renderLoading() {
    return `<div class="loading" role="status"><span class="spinner"></span>Loading registry…</div>`;
  }

  _renderContent() {
    if (!this._data) {
      return `<div class="empty"><h2>Registry unavailable</h2><p>Reload the page to try again.</p></div>`;
    }
    return `${this._renderSummary()}${this._renderFilters()}<section id="results">${this._renderResultsHtml()}</section>`;
  }

  _renderSummary() {
    const summary = this._data.summary;
    const cards = [
      [summary.total, "Tracked"],
      [summary.statuses.active || 0, "Active"],
      [summary.statuses.testing || 0, "Testing"],
      [summary.needs_review, "Need review"],
      [summary.no_known_usage, "No known usage"],
      [summary.never_reviewed, "Never reviewed"],
      [summary.uninstalled, "Uninstalled"],
    ];
    return `<section class="summary" aria-label="Registry summary">${cards
      .map(([value, label]) => `<article><strong>${value}</strong><span>${label}</span></article>`)
      .join("")}</section>`;
  }

  _renderFilters() {
    const f = this._filters;
    return `
      <section class="filters" aria-label="Filters and sorting">
        <label class="search"><span>Search</span><input data-filter="query" type="search" value="${escapeHtml(f.query)}" placeholder="Name, repository, notes, tags, usages"></label>
        <label><span>Installation</span><select data-filter="installation">
          ${option("all", "All", f.installation)}${option("installed", "Installed", f.installation)}${option("uninstalled", "Uninstalled", f.installation)}
        </select></label>
        <label><span>Status</span><select data-filter="status">
          ${option("all", "All", f.status)}${Object.entries(STATUS_LABELS).map(([value, label]) => option(value, label, f.status)).join("")}${option("none", "No status", f.status)}
        </select></label>
        <label><span>Rating</span><select data-filter="rating">
          ${option("all", "All", f.rating)}${option("3", "★★★", f.rating)}${option("2", "★★", f.rating)}${option("1", "★", f.rating)}${option("none", "No rating", f.rating)}
        </select></label>
        <label><span>Review</span><select data-filter="review">
          ${option("all", "All", f.review)}${Object.entries(REVIEW_LABELS).map(([value, label]) => option(value, label, f.review)).join("")}
        </select></label>
        <label><span>Source</span><select data-filter="source">
          ${option("all", "All", f.source)}${this._data.sources.map((value) => option(value, value.toUpperCase(), f.source)).join("")}
        </select></label>
        <label><span>Category</span><select data-filter="category">
          ${option("all", "All", f.category)}${this._data.categories.map((value) => option(value, value, f.category)).join("")}
        </select></label>
        <label><span>Tags</span><input data-filter="tags" list="filter-tags" value="${escapeHtml(f.tags)}" placeholder="dashboard, important"><datalist id="filter-tags">${this._data.tags.map((tag) => `<option value="${escapeHtml(tag)}"></option>`).join("")}</datalist></label>
        <label><span>Sort</span><select data-filter="sort">
          ${option("name", "Name", f.sort)}${option("rating", "Rating", f.sort)}${option("status", "Status", f.sort)}${option("last_reviewed", "Last reviewed", f.sort)}${option("discovered", "Discovered", f.sort)}${option("usages", "Usage count", f.sort)}${option("installed", "Installation", f.sort)}
        </select></label>
        <label><span>Direction</span><select data-filter="direction">${option("asc", "Ascending", f.direction)}${option("desc", "Descending", f.direction)}</select></label>
      </section>`;
  }

  _renderResults() {
    const container = this.shadowRoot.querySelector("#results");
    if (container) container.innerHTML = this._renderResultsHtml();
  }

  _renderResultsHtml() {
    const items = this.filteredItems;
    if (!items.length) {
      return `<div class="empty"><h2>No matching integrations</h2><p>Adjust the search or filters to see more items.</p></div>`;
    }
    return `
      <div class="result-count">${items.length} of ${this._data.items.length} integrations</div>
      <div class="table-wrap"><table>
        <thead><tr><th>Integration</th><th>Source</th><th>Category</th><th>Status</th><th>Rating</th><th>Uses</th><th>Last review</th><th>Installed</th><th>Version</th></tr></thead>
        <tbody>${items.map((item) => this._renderRow(item)).join("")}</tbody>
      </table></div>`;
  }

  _renderRow(item) {
    return `<tr class="${item.installed ? "" : "uninstalled"}" tabindex="0" data-action="open" data-item-id="${escapeHtml(item.id)}">
      <td><div class="integration-cell">${this._renderIcon(item)}<div><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.repository)}</small></div></div></td>
      <td>${escapeHtml(item.source.toUpperCase())}</td>
      <td>${escapeHtml(item.category || "—")}</td>
      <td>${this._badge(item.status ? STATUS_LABELS[item.status] : "No status")}</td>
      <td class="stars" aria-label="${item.rating ? `${item.rating} stars` : "No rating"}">${item.rating ? "★".repeat(item.rating) + "☆".repeat(3 - item.rating) : "—"}</td>
      <td>${item.usages.length}</td>
      <td>${escapeHtml(this._formatDate(item.last_reviewed_at))}<small>${escapeHtml(REVIEW_LABELS[item.review_state])}</small></td>
      <td>${this._badge(item.installed ? "Installed" : "Uninstalled", item.installed ? "success" : "muted")}</td>
      <td>${escapeHtml(item.version || "—")}</td>
    </tr>`;
  }

  _renderIcon(item) {
    if (item.icon && /^https?:\/\//i.test(item.icon)) {
      return `<img class="item-icon" src="${escapeHtml(item.icon)}" alt="">`;
    }
    return `<span class="item-icon fallback"><ha-icon icon="mdi:puzzle"></ha-icon></span>`;
  }

  _badge(text, style = "") {
    return `<span class="badge ${style}">${escapeHtml(text)}</span>`;
  }

  _renderDialog(item) {
    const editing = item.usages.find((usage) => usage.id === this._editingUsageId);
    return `<div class="overlay" data-action="close">
      <section class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title" tabindex="-1" data-action="dialog">
        <div class="dialog-head">
          <div class="integration-cell">${this._renderIcon(item)}<div><h2 id="dialog-title">${escapeHtml(item.name)}</h2><small>${escapeHtml(item.repository)}</small></div></div>
          <button class="icon-button" data-action="close" aria-label="Close details">×</button>
        </div>
        <div class="dialog-body">
          <section class="metadata">
            <h3>Provider metadata</h3>
            <dl>
              <div><dt>Source</dt><dd>${escapeHtml(item.source.toUpperCase())}</dd></div>
              <div><dt>Category</dt><dd>${escapeHtml(item.category || "—")}</dd></div>
              <div><dt>Installed</dt><dd>${item.installed ? "Yes" : "No"}</dd></div>
              <div><dt>Installed version</dt><dd>${escapeHtml(item.version || "—")}</dd></div>
              <div><dt>Available version</dt><dd>${escapeHtml(item.available_version || "—")}</dd></div>
              <div><dt>Discovered</dt><dd>${escapeHtml(this._formatDate(item.discovered_at, true))}</dd></div>
              ${item.uninstalled_at ? `<div><dt>Uninstalled</dt><dd>${escapeHtml(this._formatDate(item.uninstalled_at, true))}</dd></div>` : ""}
            </dl>
            ${item.repository_url ? `<a class="button secondary" href="${escapeHtml(item.repository_url)}" target="_blank" rel="noopener noreferrer">Open repository</a>` : ""}
          </section>
          <form id="details-form" class="editor">
            <h3>Your tracking data</h3>
            <fieldset><legend>Rating</legend><input id="rating-value" name="rating" type="hidden" value="${item.rating ?? ""}"><div class="rating-control">
              ${[1, 2, 3].map((rating) => `<button type="button" class="star-button ${rating <= (item.rating || 0) ? "selected" : ""}" data-action="rating" data-rating="${rating}" aria-label="Set ${rating} stars" aria-pressed="${rating === item.rating}">★</button>`).join("")}
              <button type="button" class="text-button" data-action="clear-rating">Clear</button>
            </div></fieldset>
            <label><span>Status</span><select name="status">${option("", "No status", item.status || "")}${Object.entries(STATUS_LABELS).map(([value, label]) => option(value, label, item.status)).join("")}</select></label>
            <label><span>Tags <small>Comma separated</small></span><input name="tags" list="known-tags" value="${escapeHtml(item.tags.join(", "))}"><datalist id="known-tags">${this._data.tags.map((tag) => `<option value="${escapeHtml(tag)}"></option>`).join("")}</datalist></label>
            <label><span>Notes</span><textarea name="notes" rows="6" placeholder="Why is this installed? What should you remember?">${escapeHtml(item.notes || "")}</textarea></label>
            <button class="primary" type="submit" ${this._saving ? "disabled" : ""}>Save details</button>
          </form>
          <section class="usages">
            <div class="section-heading"><div><h3>Known usages</h3><p>${item.usages.length} registered</p></div></div>
            ${item.usages.length ? `<ul>${item.usages.map((usage) => this._renderUsage(usage)).join("")}</ul>` : `<div class="empty compact">No known usage has been registered.</div>`}
            ${this._renderUsageForm(editing)}
          </section>
          <section class="reviews">
            <div class="section-heading"><div><h3>Reviews</h3><p>Interval: ${this._data.review_interval_days} days</p></div><button class="primary" data-action="review" ${this._saving ? "disabled" : ""}>Mark as reviewed</button></div>
            <p><strong>Last reviewed:</strong> ${escapeHtml(this._formatDate(item.last_reviewed_at, true))} · ${escapeHtml(REVIEW_LABELS[item.review_state])}</p>
            ${item.review_history.length ? `<ol>${[...item.review_history].reverse().map((review) => `<li>${escapeHtml(this._formatDate(review.reviewed_at, true))}</li>`).join("")}</ol>` : `<div class="empty compact">This integration has never been reviewed.</div>`}
          </section>
        </div>
      </section>
    </div>`;
  }

  _renderUsage(usage) {
    return `<li><div class="usage-main"><ha-icon icon="${USAGE_ICONS[usage.type] || USAGE_ICONS.other}"></ha-icon><div><strong>${escapeHtml(usage.name)}</strong><small>${escapeHtml(usage.type)}${usage.url ? ` · ${escapeHtml(usage.url)}` : ""}</small></div></div><div class="row-actions">
      ${usage.url ? `<button class="text-button" data-action="usage-link" data-url="${escapeHtml(usage.url)}">Open</button>` : ""}
      <button class="text-button" data-action="edit-usage" data-usage-id="${escapeHtml(usage.id)}">Edit</button>
      <button class="text-button danger" data-action="remove-usage" data-usage-id="${escapeHtml(usage.id)}">Remove</button>
    </div></li>`;
  }

  _renderUsageForm(usage) {
    return `<form id="usage-form" class="usage-form">
      <h4>${usage ? "Edit usage" : "Add usage"}</h4>
      <label><span>Name</span><input name="usage-name" required value="${escapeHtml(usage?.name || "")}" placeholder="Health dashboard"></label>
      <label><span>Type</span><select name="usage-type">${USAGE_TYPES.map((type) => option(type, type, usage?.type || "dashboard")).join("")}</select></label>
      <label><span>URL <small>Optional</small></span><input name="usage-url" value="${escapeHtml(usage?.url || "")}" placeholder="/dashboard-health or https://…"></label>
      <div class="form-actions"><button class="primary" type="submit" ${this._saving ? "disabled" : ""}>${usage ? "Update usage" : "Add usage"}</button>${usage ? `<button type="button" class="secondary" data-action="cancel-usage">Cancel</button>` : ""}</div>
    </form>`;
  }

  _formatDate(value, absolute = false) {
    if (!value) return "Never";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    if (absolute) return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
    const days = Math.round((date.getTime() - Date.now()) / 86400000);
    if (Math.abs(days) < 1) return "Today";
    if (Math.abs(days) < 30) return new Intl.RelativeTimeFormat(undefined, { numeric: "auto" }).format(days, "day");
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
  }

  _styles() {
    return `
      :host { display:block; min-height:100%; color:var(--primary-text-color); background:var(--primary-background-color); font-family:var(--paper-font-body1_-_font-family, sans-serif); }
      * { box-sizing:border-box; }
      main { max-width:1500px; margin:0 auto; padding:calc(24px + env(safe-area-inset-top)) calc(24px + env(safe-area-inset-right)) calc(32px + env(safe-area-inset-bottom)) calc(24px + env(safe-area-inset-left)); }
      header { display:flex; align-items:flex-start; justify-content:space-between; gap:24px; margin-bottom:24px; }
      h1,h2,h3,h4,p { margin-top:0; } h1 { margin-bottom:6px; font-size:2rem; } header p,.section-heading p { color:var(--secondary-text-color); margin-bottom:0; }
      button,.button,input,select,textarea { font:inherit; } button,.button { min-height:40px; border-radius:var(--ha-card-border-radius, 10px); padding:8px 14px; cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--divider-color); color:var(--primary-text-color); background:var(--card-background-color); }
      button:focus-visible,.button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,tr:focus-visible { outline:3px solid var(--primary-color); outline-offset:2px; }
      button:disabled { opacity:.55; cursor:wait; } button.primary { color:var(--text-primary-color); background:var(--primary-color); border-color:var(--primary-color); font-weight:600; } .secondary { background:var(--secondary-background-color); } .text-button { min-height:34px; padding:4px 8px; border-color:transparent; background:transparent; color:var(--primary-color); } .danger { color:var(--error-color); }
      .sync-block { display:flex; flex-direction:column; align-items:flex-end; gap:8px; color:var(--secondary-text-color); font-size:.9rem; }
      .summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:12px; margin-bottom:20px; }
      .summary article,.filters,.table-wrap,.metadata,.editor,.usages,.reviews { background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:var(--ha-card-border-radius, 12px); box-shadow:var(--ha-card-box-shadow, none); }
      .summary article { padding:16px; display:flex; flex-direction:column; gap:4px; } .summary strong { font-size:1.65rem; color:var(--primary-color); } .summary span { color:var(--secondary-text-color); }
      .filters { display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:12px; padding:16px; margin-bottom:18px; } .filters .search { grid-column:span 2; }
      label { display:flex; flex-direction:column; gap:6px; font-size:.9rem; } label>span,legend { font-weight:600; } label small { color:var(--secondary-text-color); font-weight:400; }
      input,select,textarea { width:100%; color:var(--primary-text-color); background:var(--input-fill-color, var(--secondary-background-color)); border:1px solid var(--input-idle-line-color, var(--divider-color)); border-radius:8px; padding:10px 12px; } textarea { resize:vertical; }
      .result-count { color:var(--secondary-text-color); margin:0 0 8px 4px; } .table-wrap { overflow:auto; } table { width:100%; border-collapse:collapse; min-width:980px; } th,td { padding:13px 12px; text-align:left; border-bottom:1px solid var(--divider-color); } th { color:var(--secondary-text-color); font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; } tbody tr { cursor:pointer; } tbody tr:hover { background:var(--secondary-background-color); } tbody tr:last-child td { border-bottom:0; } tr.uninstalled { opacity:.72; }
      .integration-cell { display:flex; align-items:center; gap:12px; min-width:200px; } .integration-cell strong,.integration-cell small { display:block; } .integration-cell small,td small { color:var(--secondary-text-color); margin-top:3px; }
      .item-icon { width:40px; height:40px; object-fit:contain; flex:0 0 40px; border-radius:8px; } .item-icon.fallback { display:grid; place-items:center; color:var(--primary-color); background:var(--secondary-background-color); }
      .badge { display:inline-flex; border:1px solid var(--divider-color); background:var(--secondary-background-color); border-radius:999px; padding:3px 9px; white-space:nowrap; } .badge.success { color:var(--success-color); } .badge.muted { color:var(--secondary-text-color); } .stars,.star-button.selected { color:var(--warning-color); }
      .message { border:1px solid var(--divider-color); border-left:4px solid var(--primary-color); background:var(--card-background-color); border-radius:8px; padding:12px 14px; margin-bottom:16px; } .message.error { border-left-color:var(--error-color); } .message.warning { border-left-color:var(--warning-color); }
      .loading,.empty { text-align:center; padding:56px 24px; color:var(--secondary-text-color); } .loading { display:flex; justify-content:center; gap:10px; } .spinner { width:20px; height:20px; border:2px solid var(--divider-color); border-top-color:var(--primary-color); border-radius:50%; animation:spin .8s linear infinite; } @keyframes spin { to { transform:rotate(360deg); } }
      .overlay { position:fixed; z-index:10; inset:0; background:var(--mdc-dialog-scrim-color, rgba(0,0,0,.45)); display:flex; justify-content:flex-end; } .dialog { width:min(720px,100%); height:100%; overflow:auto; background:var(--primary-background-color); box-shadow:var(--ha-card-box-shadow); }
      .dialog-head { position:sticky; top:0; z-index:1; display:flex; align-items:center; justify-content:space-between; gap:16px; padding:18px 22px; border-bottom:1px solid var(--divider-color); background:var(--app-header-background-color, var(--card-background-color)); color:var(--app-header-text-color, var(--primary-text-color)); } .dialog-head h2 { margin-bottom:3px; } .icon-button { font-size:1.7rem; min-width:42px; padding:0; border-color:transparent; background:transparent; }
      .dialog-body { display:grid; gap:16px; padding:18px 22px calc(28px + env(safe-area-inset-bottom)); } .metadata,.editor,.usages,.reviews { padding:18px; } dl { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; } dl div { min-width:0; } dt { color:var(--secondary-text-color); font-size:.8rem; } dd { margin:3px 0 0; overflow-wrap:anywhere; }
      .editor { display:grid; gap:14px; } fieldset { border:0; padding:0; margin:0; } .rating-control { display:flex; align-items:center; gap:2px; margin-top:5px; } .star-button { border:0; background:transparent; font-size:1.8rem; padding:2px; color:var(--disabled-text-color); }
      .section-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; } .section-heading h3 { margin-bottom:3px; } .usages ul { list-style:none; margin:12px 0 18px; padding:0; } .usages li { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:11px 0; border-bottom:1px solid var(--divider-color); } .usage-main { display:flex; align-items:center; gap:10px; min-width:0; } .usage-main strong,.usage-main small { display:block; overflow-wrap:anywhere; } .usage-main small { color:var(--secondary-text-color); margin-top:3px; } .row-actions { display:flex; flex-wrap:wrap; justify-content:flex-end; }
      .usage-form { display:grid; grid-template-columns:2fr 1fr; gap:12px; padding-top:8px; } .usage-form h4,.usage-form label:last-of-type,.form-actions { grid-column:1/-1; } .form-actions { display:flex; gap:8px; } .empty.compact { padding:18px; background:var(--secondary-background-color); border-radius:8px; } .reviews ol { margin-bottom:0; }
      .sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; }
      @media (max-width:800px) { main { padding:16px; } header { flex-direction:column; } .sync-block { align-items:flex-start; } .filters .search { grid-column:1/-1; } th:nth-child(3),td:nth-child(3),th:nth-child(6),td:nth-child(6),th:nth-child(9),td:nth-child(9) { display:none; } table { min-width:690px; } .dialog-head,.dialog-body { padding-left:14px; padding-right:14px; } dl { grid-template-columns:1fr; } .usages li { align-items:flex-start; flex-direction:column; } .row-actions { justify-content:flex-start; } }
      @media (max-width:520px) { .filters { grid-template-columns:1fr; } .filters .search { grid-column:auto; } .usage-form { grid-template-columns:1fr; } .usage-form h4,.usage-form label:last-of-type,.form-actions { grid-column:auto; } }
    `;
  }
}

if (!customElements.get("integration-tracker-panel")) {
  customElements.define("integration-tracker-panel", IntegrationTrackerPanel);
}
