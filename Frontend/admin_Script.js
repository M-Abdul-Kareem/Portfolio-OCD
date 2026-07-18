/* ════════════════════════════════════════════════════════════
   CONFIG — change this to your deployed API URL when you host it.
   ════════════════════════════════════════════════════════════ */
const API_BASE = "http://127.0.0.1:8000";

/* ── Auth token is kept in sessionStorage: cleared when the
   browser tab closes, but survives a page refresh while working. ── */
function getToken() { return sessionStorage.getItem("admin_token"); }
function setToken(t) { sessionStorage.setItem("admin_token", t); }
function clearToken() { sessionStorage.removeItem("admin_token"); }

/* ── Generic API helper. Adds auth header automatically.
   Logs the admin out automatically if the token has expired.
   Also transparently handles 2FA: if the server responds 428
   Precondition Required, this shows the code-entry popup, then
   resubmits the EXACT SAME request with the verification headers
   attached — every caller (loadX/saveX/deleteX) gets 2FA support
   for free, with no changes needed at the call site. ── */
async function api(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
  }

  async function doFetch(extraHeaders = {}) {
    return fetch(API_BASE + path, {
      method,
      headers: { ...headers, ...extraHeaders },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  let res;
  try {
    res = await doFetch();
  } catch (networkErr) {
    throw new Error(`Could not reach the backend (${networkErr.message}). Is uvicorn running on port 8000?`);
  }

  if (res.status === 401 && auth) {
    clearToken();
    showLogin();
    throw new Error("Session expired. Please log in again.");
  }

  if (res.status === 428) {
    res = await handle2FAChallenge(res, doFetch);
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = Array.isArray(data.detail)
      ? data.detail.map(d => d.msg).join(", ")
      : (data.detail || "Something went wrong.");
    throw new Error(msg);
  }
  return data;
}

/* ── Shared 2FA challenge handler ──
   Used by both api() (JSON requests) and the raw fetch() calls
   (like photo upload, which uses multipart/form-data). Takes the
   428 response plus a retry function, prompts for the code, and
   returns the final response after resubmitting with the code. ── */
async function handle2FAChallenge(res428, doFetch) {
  const data = await res428.json().catch(() => ({}));
  const detail = data.detail || {};
  const pendingId = detail.pending_id;

  if (!pendingId) {
    // Shouldn't happen, but fail safely rather than loop forever.
    throw new Error(detail.message || "Verification required, but no pending ID was returned.");
  }

  // Loop lets the admin retry after a wrong code without restarting
  // the whole action (the server allows MAX_CODE_ATTEMPTS attempts
  // against the same pending_id before it's invalidated).
  while (true) {
    const code = await promptFor2FACode(detail.message || "Enter the 6-digit code sent to your email.");
    if (!code) {
      throw new Error("Action cancelled — verification code required.");
    }

    let retryRes;
    try {
      retryRes = await doFetch({ "X-2FA-Pending-Id": pendingId, "X-2FA-Code": code });
    } catch (networkErr) {
      // A network-level failure (server dropped, wifi blip, etc.) — NOT
      // a wrong code. The pending_id + code are still valid server-side,
      // so re-open the prompt with the SAME code prefilled instead of
      // forcing the admin to restart the whole action from scratch.
      const retry = confirm(
        "Network error while confirming — your code may still be valid.\n\n" +
        "Click OK to try sending it again, or Cancel to give up."
      );
      if (!retry) {
        throw new Error("Action cancelled after a network error.");
      }
      continue; // loop back to promptFor2FACode and try again
    }

    if (retryRes.ok || retryRes.status === 204) {
      return retryRes;
    }

    // Wrong code, expired, or too many attempts — show why, then loop
    // back to ask again UNLESS the pending action itself is now dead
    // (expired / too many attempts), in which case surface the error.
    const errData = await retryRes.clone().json().catch(() => ({}));
    const errMsg = errData.detail || "Verification failed.";

    if (retryRes.status === 400) {
      // Pending action is gone (expired, too many attempts, or already used)
      throw new Error(errMsg);
    }

    // status 401 = wrong code, still has attempts left — loop and ask again
    show2FAError(errMsg);
  }
}

/* ── Code-entry modal ──
   Returns a Promise<string|null> — null if the admin cancels. ── */
function promptFor2FACode(message) {
  return new Promise((resolve) => {
    const overlay = document.getElementById("twoFAOverlay");
    const msgEl = document.getElementById("twoFAMessage");
    const errEl = document.getElementById("twoFAError");
    const input = document.getElementById("twoFACodeInput");
    const form = document.getElementById("twoFAForm");
    const cancelBtn = document.getElementById("twoFACancelBtn");

    msgEl.textContent = message;
    errEl.textContent = "";
    input.value = "";
    overlay.hidden = false;
    const openedAt = Date.now();
    setTimeout(() => input.focus(), 50);

    function cleanup() {
      overlay.hidden = true;
      form.onsubmit = null;
      cancelBtn.onclick = null;
    }

    form.onsubmit = (e) => {
      e.preventDefault();

      // Guard 1: ignore submissions not directly caused by a real user
      // action (a browser feature or extension calling form.submit()
      // programmatically produces an untrusted event; a genuine click
      // or Enter keypress does not).
      if (!e.isTrusted) {
        console.warn("Ignored an untrusted 2FA form submission (likely browser/extension auto-fill).");
        return;
      }

      // Guard 2: no human can read a freshly emailed code, switch
      // windows, and type+submit 6 digits in under ~400ms. A near-
      // instant submit this fast is a strong sign of autofill/auto-
      // submit behavior hijacking the form, not a real person typing.
      if (Date.now() - openedAt < 400) {
        console.warn("Ignored a suspiciously fast 2FA submission (possible autofill).");
        return;
      }

      const val = input.value.trim();
      if (!/^\d{6}$/.test(val)) {
        errEl.textContent = "Enter the 6-digit code.";
        return;
      }
      cleanup();
      resolve(val);
    };

    cancelBtn.onclick = () => {
      cleanup();
      resolve(null);
    };
  });
}

function show2FAError(message) {
  const errEl = document.getElementById("twoFAError");
  const input = document.getElementById("twoFACodeInput");
  errEl.textContent = message;
  input.value = "";
  input.focus();
}

/* ── Toast notifications ── */
let toastTimer;
function toast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.toggle("error", isError);
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3000);
}

/* ════════════════════════════════════════════════════════════
   LOGIN / LOGOUT
   ════════════════════════════════════════════════════════════ */
function showLogin() {
  document.getElementById("loginScreen").hidden = false;
  document.getElementById("dashboard").hidden = true;
}

function showDashboard() {
  document.getElementById("loginScreen").hidden = true;
  document.getElementById("dashboard").hidden = false;
  loadAllPanels();
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const errorEl = document.getElementById("loginError");
  const btn = document.getElementById("loginBtn");
  errorEl.textContent = "";
  btn.disabled = true;
  btn.textContent = "Logging in…";

  try {
    const data = await api("/api/auth/login", { method: "POST", body: { username, password } });
    setToken(data.access_token);
    showDashboard();
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Log In →";
  }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearToken();
  showLogin();
});

/* ════════════════════════════════════════════════════════════
   SIDEBAR NAVIGATION
   ════════════════════════════════════════════════════════════ */
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const panelName = btn.dataset.panel;
    document.querySelectorAll(".panel").forEach(p => p.hidden = true);
    document.getElementById("panel-" + panelName).hidden = false;
  });
});

/* ════════════════════════════════════════════════════════════
   HERO PANEL
   ════════════════════════════════════════════════════════════ */
async function loadHero() {
  const hero = await api("/api/hero");
  document.getElementById("hero_name1").value = hero.name_line1 || "";
  document.getElementById("hero_name2").value = hero.name_line2 || "";
  document.getElementById("hero_badge").value = hero.badge_text || "";
  document.getElementById("hero_roles").value = (hero.roles || []).join("\n");
  document.getElementById("hero_bio").value = hero.bio || "";
  document.getElementById("hero_email").value = hero.email || "";
  document.getElementById("hero_phone").value = hero.phone || "";
  document.getElementById("hero_li_label").value = hero.linkedin_label || "";
  document.getElementById("hero_li_url").value = hero.linkedin_url || "";
}

document.getElementById("heroForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/hero", {
      method: "PUT",
      auth: true,
      body: {
        name_line1: document.getElementById("hero_name1").value,
        name_line2: document.getElementById("hero_name2").value,
        badge_text: document.getElementById("hero_badge").value,
        roles: document.getElementById("hero_roles").value.split("\n").map(s => s.trim()).filter(Boolean),
        bio: document.getElementById("hero_bio").value,
        email: document.getElementById("hero_email").value,
        phone: document.getElementById("hero_phone").value,
        linkedin_label: document.getElementById("hero_li_label").value,
        linkedin_url: document.getElementById("hero_li_url").value,
      },
    });
    toast("Hero section saved.");
  } catch (err) { toast(err.message, true); }
});

/* ════════════════════════════════════════════════════════════
   ABOUT PANEL
   ════════════════════════════════════════════════════════════ */
let currentPhotoUrl = "";

async function loadAbout() {
  const about = await api("/api/about");
  document.getElementById("about_heading").value = about.heading || "";
  document.getElementById("about_paragraphs").value = (about.paragraphs || []).join("\n");
  document.getElementById("about_degree").value = about.degree || "";
  document.getElementById("about_semester").value = about.semester || "";
  document.getElementById("about_cgpa").value = about.cgpa || "";
  document.getElementById("about_location").value = about.location || "";

  currentPhotoUrl = about.photo_url || "";
  if (currentPhotoUrl) {
    document.getElementById("photoPreviewImg").src = API_BASE + currentPhotoUrl;
    document.getElementById("photoPreviewImg").hidden = false;
    document.getElementById("photoPreviewEmoji").hidden = true;
  }
}

document.getElementById("aboutForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/about", {
      method: "PUT",
      auth: true,
      body: {
        heading: document.getElementById("about_heading").value,
        paragraphs: document.getElementById("about_paragraphs").value.split("\n").map(s => s.trim()).filter(Boolean),
        photo_url: currentPhotoUrl,
        degree: document.getElementById("about_degree").value,
        semester: document.getElementById("about_semester").value,
        cgpa: document.getElementById("about_cgpa").value,
        location: document.getElementById("about_location").value,
      },
    });
    toast("About section saved.");
  } catch (err) { toast(err.message, true); }
});

/* ── PHOTO UPLOAD ── */
const photoInput = document.getElementById("photoInput");
const photoUploadBtn = document.getElementById("photoUploadBtn");

photoUploadBtn.addEventListener("click", () => photoInput.click());

photoInput.addEventListener("change", async () => {
  const file = photoInput.files[0];
  if (!file) return;

  // Client-side checks first (fast feedback) — the server re-validates
  // everything regardless, since the client can never be trusted alone.
  const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
  if (!allowed.includes(file.type)) {
    toast("Unsupported file type. Use JPEG, PNG, WEBP, or GIF.", true);
    photoInput.value = "";
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    toast("File too large. Maximum size is 5MB.", true);
    photoInput.value = "";
    return;
  }

  photoUploadBtn.disabled = true;
  photoUploadBtn.textContent = "Uploading…";

  try {
    const formData = new FormData();
    formData.append("file", file);
    const token = getToken();

    async function doUploadFetch(extraHeaders = {}) {
      return fetch(API_BASE + "/api/about/photo", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token, ...extraHeaders },  // NOTE: no Content-Type —
        body: formData,                                                     // the browser sets the
      });                                                                    // multipart boundary automatically.
    }

    let res;
    try {
      res = await doUploadFetch();
    } catch (networkErr) {
      throw new Error(`Could not reach the backend (${networkErr.message}). Is uvicorn running on port 8000?`);
    }

    if (res.status === 401) {
      clearToken();
      showLogin();
      throw new Error("Session expired. Please log in again.");
    }

    if (res.status === 428) {
      res = await handle2FAChallenge(res, doUploadFetch);
    }

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Upload failed.");
    }

    currentPhotoUrl = data.photo_url;
    document.getElementById("photoPreviewImg").src = API_BASE + currentPhotoUrl + "?t=" + Date.now();
    document.getElementById("photoPreviewImg").hidden = false;
    document.getElementById("photoPreviewEmoji").hidden = true;
    toast("Photo uploaded. Don't forget it's already saved — no need to click 'Save About Section'.");

  } catch (err) {
    toast(err.message, true);
  } finally {
    photoUploadBtn.disabled = false;
    photoUploadBtn.textContent = "Choose Photo…";
    photoInput.value = "";
  }
});

/* ════════════════════════════════════════════════════════════
   CONTACT INFO PANEL
   ════════════════════════════════════════════════════════════ */
async function loadContactInfo() {
  const info = await api("/api/contact-info");
  document.getElementById("ci_email").value = info.email || "";
  document.getElementById("ci_phone").value = info.phone || "";
  document.getElementById("ci_location").value = info.location || "";
  document.getElementById("ci_li_label").value = info.linkedin_label || "";
  document.getElementById("ci_li_url").value = info.linkedin_url || "";
}

document.getElementById("contactInfoForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/contact-info", {
      method: "PUT",
      auth: true,
      body: {
        email: document.getElementById("ci_email").value,
        phone: document.getElementById("ci_phone").value,
        location: document.getElementById("ci_location").value,
        linkedin_label: document.getElementById("ci_li_label").value,
        linkedin_url: document.getElementById("ci_li_url").value,
      },
    });
    toast("Contact info saved.");
  } catch (err) { toast(err.message, true); }
});

/* ════════════════════════════════════════════════════════════
   GENERIC MODAL (used for Skills / Experience / Projects)
   ════════════════════════════════════════════════════════════ */
const modalOverlay = document.getElementById("modalOverlay");
const modalTitle = document.getElementById("modalTitle");
const modalForm = document.getElementById("modalForm");

function openModal(title, fieldsHtml, onSubmit) {
  modalTitle.textContent = title;
  modalForm.innerHTML = fieldsHtml + `
    <div class="modal-actions">
      <button type="button" class="btn-secondary" id="modalCancel">Cancel</button>
      <button type="submit" class="btn-primary">Save</button>
    </div>`;
  modalOverlay.hidden = false;
  document.getElementById("modalCancel").addEventListener("click", closeModal);
  modalForm.onsubmit = async (e) => {
    e.preventDefault();
    try {
      await onSubmit();
      closeModal();
    } catch (err) {
      toast(err.message, true);
    }
  };
}

function closeModal() {
  modalOverlay.hidden = true;
  modalForm.onsubmit = null;
}

modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeModal();
});

/* ════════════════════════════════════════════════════════════
   SKILLS PANEL
   ════════════════════════════════════════════════════════════ */
async function loadSkills() {
  const skills = await api("/api/skills");
  const list = document.getElementById("skillsList");
  if (skills.length === 0) {
    list.innerHTML = `<div class="empty-state">No skill categories yet. Click "+ Add Category" to create one.</div>`;
    return;
  }
  list.innerHTML = skills.map(s => `
    <div class="list-card">
      <div class="list-card-info">
        <div class="list-card-title">${s.icon || ""} ${escapeHtml(s.title)}</div>
        <div class="list-card-tags">${(s.tags || []).map(t => `<span class="mini-tag">${escapeHtml(t)}</span>`).join("")}</div>
      </div>
      <div class="list-card-actions">
        <button class="icon-btn" title="Edit" data-edit="${s.id}">✏️</button>
        <button class="icon-btn danger" title="Delete" data-delete="${s.id}">🗑️</button>
      </div>
    </div>
  `).join("");

  list.querySelectorAll("[data-edit]").forEach(btn =>
    btn.addEventListener("click", () => editSkill(skills.find(s => s.id == btn.dataset.edit))));
  list.querySelectorAll("[data-delete]").forEach(btn =>
    btn.addEventListener("click", () => deleteSkill(btn.dataset.delete)));
}

function skillFieldsHtml(s = {}) {
  return `
    <div class="form-group"><label>Icon (emoji)</label><input type="text" id="m_icon" value="${escapeHtml(s.icon || "💻")}" /></div>
    <div class="form-group"><label>Title</label><input type="text" id="m_title" value="${escapeHtml(s.title || "")}" required /></div>
    <div class="form-group"><label>Tags (one per line)</label><textarea id="m_tags" rows="5">${(s.tags || []).join("\n")}</textarea></div>
    <div class="form-group"><label>Sort order</label><input type="number" id="m_order" value="${s.sort_order ?? 0}" /></div>
  `;
}

function editSkill(skill) {
  openModal("Edit Skill Category", skillFieldsHtml(skill), async () => {
    await api(`/api/skills/${skill.id}`, {
      method: "PUT", auth: true,
      body: {
        icon: document.getElementById("m_icon").value,
        title: document.getElementById("m_title").value,
        tags: document.getElementById("m_tags").value.split("\n").map(s => s.trim()).filter(Boolean),
        sort_order: Number(document.getElementById("m_order").value) || 0,
      },
    });
    toast("Skill category updated.");
    loadSkills();
  });
}

document.getElementById("addSkillBtn").addEventListener("click", () => {
  openModal("Add Skill Category", skillFieldsHtml(), async () => {
    await api("/api/skills", {
      method: "POST", auth: true,
      body: {
        icon: document.getElementById("m_icon").value,
        title: document.getElementById("m_title").value,
        tags: document.getElementById("m_tags").value.split("\n").map(s => s.trim()).filter(Boolean),
        sort_order: Number(document.getElementById("m_order").value) || 0,
      },
    });
    toast("Skill category added.");
    loadSkills();
  });
});

async function deleteSkill(id) {
  if (!confirm("Delete this skill category?")) return;
  try {
    await api(`/api/skills/${id}`, { method: "DELETE", auth: true });
    toast("Skill category deleted.");
    loadSkills();
  } catch (err) { toast(err.message, true); }
}

/* ════════════════════════════════════════════════════════════
   EXPERIENCE PANEL
   ════════════════════════════════════════════════════════════ */
async function loadExperience() {
  const items = await api("/api/experience");
  const list = document.getElementById("experienceList");
  if (items.length === 0) {
    list.innerHTML = `<div class="empty-state">No experience entries yet. Click "+ Add Entry" to create one.</div>`;
    return;
  }
  list.innerHTML = items.map(item => `
    <div class="list-card">
      <div class="list-card-info">
        <div class="list-card-title">${escapeHtml(item.title)}</div>
        <div class="list-card-sub">${escapeHtml(item.date_range)} · ${escapeHtml(item.organization)}</div>
        <div class="list-card-tags">${(item.tools || []).map(t => `<span class="mini-tag">${escapeHtml(t)}</span>`).join("")}</div>
      </div>
      <div class="list-card-actions">
        <button class="icon-btn" title="Edit" data-edit="${item.id}">✏️</button>
        <button class="icon-btn danger" title="Delete" data-delete="${item.id}">🗑️</button>
      </div>
    </div>
  `).join("");

  list.querySelectorAll("[data-edit]").forEach(btn =>
    btn.addEventListener("click", () => editExperience(items.find(i => i.id == btn.dataset.edit))));
  list.querySelectorAll("[data-delete]").forEach(btn =>
    btn.addEventListener("click", () => deleteExperience(btn.dataset.delete)));
}

function expFieldsHtml(item = {}) {
  return `
    <div class="form-group"><label>Date range</label><input type="text" id="m_date" value="${escapeHtml(item.date_range || "")}" placeholder="2025 – 2026" /></div>
    <div class="form-group"><label>Title</label><input type="text" id="m_title" value="${escapeHtml(item.title || "")}" required /></div>
    <div class="form-group"><label>Organization</label><input type="text" id="m_org" value="${escapeHtml(item.organization || "")}" /></div>
    <div class="form-group"><label>Bullet points (one per line)</label><textarea id="m_bullets" rows="5">${(item.bullets || []).join("\n")}</textarea></div>
    <div class="form-group"><label>Tools (one per line, optional)</label><textarea id="m_tools" rows="3">${(item.tools || []).join("\n")}</textarea></div>
    <div class="form-group"><label>Sort order</label><input type="number" id="m_order" value="${item.sort_order ?? 0}" /></div>
  `;
}

function readExpForm() {
  return {
    date_range: document.getElementById("m_date").value,
    title: document.getElementById("m_title").value,
    organization: document.getElementById("m_org").value,
    bullets: document.getElementById("m_bullets").value.split("\n").map(s => s.trim()).filter(Boolean),
    tools: document.getElementById("m_tools").value.split("\n").map(s => s.trim()).filter(Boolean),
    sort_order: Number(document.getElementById("m_order").value) || 0,
  };
}

function editExperience(item) {
  openModal("Edit Experience Entry", expFieldsHtml(item), async () => {
    await api(`/api/experience/${item.id}`, { method: "PUT", auth: true, body: readExpForm() });
    toast("Experience entry updated.");
    loadExperience();
  });
}

document.getElementById("addExpBtn").addEventListener("click", () => {
  openModal("Add Experience Entry", expFieldsHtml(), async () => {
    await api("/api/experience", { method: "POST", auth: true, body: readExpForm() });
    toast("Experience entry added.");
    loadExperience();
  });
});

async function deleteExperience(id) {
  if (!confirm("Delete this experience entry?")) return;
  try {
    await api(`/api/experience/${id}`, { method: "DELETE", auth: true });
    toast("Experience entry deleted.");
    loadExperience();
  } catch (err) { toast(err.message, true); }
}

/* ════════════════════════════════════════════════════════════
   PROJECTS PANEL
   ════════════════════════════════════════════════════════════ */
async function loadProjects() {
  const projects = await api("/api/projects");
  const list = document.getElementById("projectsList");
  if (projects.length === 0) {
    list.innerHTML = `<div class="empty-state">No projects yet. Click "+ Add Project" to create one.</div>`;
    return;
  }
  list.innerHTML = projects.map(p => `
    <div class="list-card">
      <div class="list-card-info">
        <div class="list-card-title">${p.icon || ""} ${escapeHtml(p.title)}</div>
        <div class="list-card-sub">${escapeHtml(p.period)}</div>
        <div class="list-card-tags">${(p.tags || []).map(t => `<span class="mini-tag">${escapeHtml(t)}</span>`).join("")}</div>
      </div>
      <div class="list-card-actions">
        <button class="icon-btn" title="Edit" data-edit="${p.id}">✏️</button>
        <button class="icon-btn danger" title="Delete" data-delete="${p.id}">🗑️</button>
      </div>
    </div>
  `).join("");

  list.querySelectorAll("[data-edit]").forEach(btn =>
    btn.addEventListener("click", () => editProject(projects.find(p => p.id == btn.dataset.edit))));
  list.querySelectorAll("[data-delete]").forEach(btn =>
    btn.addEventListener("click", () => deleteProject(btn.dataset.delete)));
}

function projectFieldsHtml(p = {}) {
  return `
    <div class="form-group"><label>Icon (emoji)</label><input type="text" id="m_icon" value="${escapeHtml(p.icon || "💼")}" /></div>
    <div class="form-group"><label>Period</label><input type="text" id="m_period" value="${escapeHtml(p.period || "")}" placeholder="2026" /></div>
    <div class="form-group"><label>Title</label><input type="text" id="m_title" value="${escapeHtml(p.title || "")}" required /></div>
    <div class="form-group"><label>Description</label><textarea id="m_desc" rows="4">${escapeHtml(p.description || "")}</textarea></div>
    <div class="form-group"><label>Tags (one per line)</label><textarea id="m_tags" rows="4">${(p.tags || []).join("\n")}</textarea></div>
    <div class="form-group"><label>GitHub URL</label><input type="text" id="m_github" value="${escapeHtml(p.github_url || "")}" /></div>
    <div class="form-group"><label>Sort order</label><input type="number" id="m_order" value="${p.sort_order ?? 0}" /></div>
  `;
}

function readProjectForm() {
  return {
    icon: document.getElementById("m_icon").value,
    period: document.getElementById("m_period").value,
    title: document.getElementById("m_title").value,
    description: document.getElementById("m_desc").value,
    tags: document.getElementById("m_tags").value.split("\n").map(s => s.trim()).filter(Boolean),
    github_url: document.getElementById("m_github").value,
    sort_order: Number(document.getElementById("m_order").value) || 0,
  };
}

function editProject(p) {
  openModal("Edit Project", projectFieldsHtml(p), async () => {
    await api(`/api/projects/${p.id}`, { method: "PUT", auth: true, body: readProjectForm() });
    toast("Project updated.");
    loadProjects();
  });
}

document.getElementById("addProjectBtn").addEventListener("click", () => {
  openModal("Add Project", projectFieldsHtml(), async () => {
    await api("/api/projects", { method: "POST", auth: true, body: readProjectForm() });
    toast("Project added.");
    loadProjects();
  });
});

async function deleteProject(id) {
  if (!confirm("Delete this project?")) return;
  try {
    await api(`/api/projects/${id}`, { method: "DELETE", auth: true });
    toast("Project deleted.");
    loadProjects();
  } catch (err) { toast(err.message, true); }
}

/* ════════════════════════════════════════════════════════════
   MESSAGES PANEL
   ════════════════════════════════════════════════════════════ */
async function loadMessages() {
  const messages = await api("/api/messages", { auth: true });
  const list = document.getElementById("messagesList");
  const badge = document.getElementById("msgBadge");

  const unreadCount = messages.filter(m => !m.is_read).length;
  if (unreadCount > 0) {
    badge.hidden = false;
    badge.textContent = unreadCount;
  } else {
    badge.hidden = true;
  }

  if (messages.length === 0) {
    list.innerHTML = `<div class="empty-state">No messages yet. They'll appear here when someone uses your contact form.</div>`;
    return;
  }

  list.innerHTML = messages.map(m => `
    <div class="message-card ${m.is_read ? "" : "unread"}" data-id="${m.id}">
      <div class="message-top">
        <div>
          <div class="message-from">${escapeHtml(m.first_name)} ${escapeHtml(m.last_name)}</div>
          <div class="message-email">${escapeHtml(m.email)}</div>
        </div>
        <div class="message-date">${new Date(m.created_at).toLocaleString()}</div>
      </div>
      <div class="message-subject">${escapeHtml(m.subject)}</div>
      <div class="message-body">${escapeHtml(m.message)}</div>
      <div class="list-card-actions">
        ${!m.is_read ? `<button class="btn-secondary" data-read="${m.id}">Mark as read</button>` : ""}
        <button class="btn-danger" data-delmsg="${m.id}">Delete</button>
      </div>
    </div>
  `).join("");

  list.querySelectorAll("[data-read]").forEach(btn =>
    btn.addEventListener("click", () => markMessageRead(btn.dataset.read)));
  list.querySelectorAll("[data-delmsg]").forEach(btn =>
    btn.addEventListener("click", () => deleteMessage(btn.dataset.delmsg)));
}

async function markMessageRead(id) {
  try {
    await api(`/api/messages/${id}/read`, { method: "PATCH", auth: true });
    loadMessages();
  } catch (err) { toast(err.message, true); }
}

async function deleteMessage(id) {
  if (!confirm("Delete this message?")) return;
  try {
    await api(`/api/messages/${id}`, { method: "DELETE", auth: true });
    toast("Message deleted.");
    loadMessages();
  } catch (err) { toast(err.message, true); }
}

/* ════════════════════════════════════════════════════════════
   UTILITIES
   ════════════════════════════════════════════════════════════ */
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* ════════════════════════════════════════════════════════════
   ACCOUNT PANEL — change username/password
   ════════════════════════════════════════════════════════════ */
document.getElementById("accountForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const currentPassword = document.getElementById("acc_current_password").value;
  const newUsername = document.getElementById("acc_new_username").value.trim();
  const newPassword = document.getElementById("acc_new_password").value;

  if (!newUsername && !newPassword) {
    toast("Enter a new username and/or a new password to change something.", true);
    return;
  }
  if (newPassword && newPassword.length < 8) {
    toast("New password must be at least 8 characters.", true);
    return;
  }

  const submitBtn = e.target.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  submitBtn.textContent = "Updating…";

  try {
    const body = { current_password: currentPassword };
    if (newUsername) body.new_username = newUsername;
    if (newPassword) body.new_password = newPassword;

    await api("/api/auth/credentials", { method: "PUT", auth: true, body });

    toast("Credentials updated. Please log in again with your new details.");
    document.getElementById("accountForm").reset();

    // Username/password just changed underneath the current session —
    // force a fresh login so the admin re-authenticates with the new values.
    setTimeout(() => {
      clearToken();
      showLogin();
    }, 1500);

  } catch (err) {
    toast(err.message, true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Update Credentials";
  }
});

async function loadAllPanels() {
  // Run each panel load independently — if one fails (e.g. a single
  // endpoint is down), the others still render correctly instead of
  // the whole dashboard showing "failed to fetch".
  const loads = [
    loadHero(),
    loadAbout(),
    loadSkills(),
    loadExperience(),
    loadProjects(),
    loadContactInfo(),
    loadMessages(),
  ];

  const results = await Promise.allSettled(loads);
  const failed = results.filter(r => r.status === "rejected");

  if (failed.length === results.length) {
    // Every single call failed — backend is almost certainly not running
    toast("⚠ Could not reach the backend. Is uvicorn running on port 8000?", true);
  } else if (failed.length > 0) {
    // Some failed — show a softer warning
    toast(`${failed.length} panel(s) failed to load. Check the backend.`, true);
  }
}

/* ════════════════════════════════════════════════════════════
   INIT — check if already logged in (token in sessionStorage)
   ════════════════════════════════════════════════════════════ */
(function init() {
  if (getToken()) {
    showDashboard();
  } else {
    showLogin();
  }
})();
