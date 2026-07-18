/* ════════════════════════════════════════════════════════════
   CONFIG — point this at your running backend.
   Change this when you deploy the API somewhere other than localhost.
   ════════════════════════════════════════════════════════════ */
const API_BASE = "http://127.0.0.1:8000";

/* ── 1. THEME TOGGLE ──────────────────────── (unchanged from before) */
const html         = document.documentElement;
const themeToggle  = document.getElementById('themeToggle');
const savedTheme   = localStorage.getItem('theme') || 'dark';
html.setAttribute('data-theme', savedTheme);

themeToggle.addEventListener('click', () => {
  const current = html.getAttribute('data-theme');
  const next    = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  themeToggle.setAttribute('aria-label', `Switch to ${current} mode`);
});

/* ── 2. HAMBURGER MENU ──────────────────────── (unchanged from before) */
const hamburger    = document.getElementById('hamburger');
const mobileMenu    = document.getElementById('mobile-menu');
const menuBackdrop  = document.getElementById('menuBackdrop');

function closeMobileMenu() {
  mobileMenu.classList.remove('open');
  menuBackdrop.classList.remove('open');
  hamburger.classList.remove('open');
  hamburger.setAttribute('aria-expanded', 'false');
  hamburger.setAttribute('aria-label', 'Open menu');
}

hamburger.addEventListener('click', () => {
  const isOpen = mobileMenu.classList.toggle('open');
  menuBackdrop.classList.toggle('open', isOpen);
  hamburger.classList.toggle('open', isOpen);
  hamburger.setAttribute('aria-expanded', String(isOpen));
  hamburger.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
});

menuBackdrop.addEventListener('click', closeMobileMenu);

mobileMenu.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', closeMobileMenu);
});

/* ── 3. TYPING EFFECT ──────────────────────────────────────────
   Default roles used as a fallback if the API is unreachable.
   Replaced with live data from /api/hero once it loads (see loadHero). */
let roles = ['Full Stack Developer', 'Backend Engineer', 'Data Enthusiast', 'ASP.NET Developer', 'Problem Solver'];
const typedEl = document.getElementById('typed');
let rIndex = 0, cIndex = 0, deleting = false, typingStarted = false;

function type() {
  const current = roles[rIndex];
  if (!deleting) {
    typedEl.textContent = current.slice(0, ++cIndex);
    if (cIndex === current.length) {
      deleting = true;
      setTimeout(type, 1800);
      return;
    }
  } else {
    typedEl.textContent = current.slice(0, --cIndex);
    if (cIndex === 0) {
      deleting = false;
      rIndex   = (rIndex + 1) % roles.length;
    }
  }
  setTimeout(type, deleting ? 55 : 90);
}

function startTyping() {
  if (typingStarted) return;   // only ever start the loop once
  typingStarted = true;
  type();
}

/* ── 4. SCROLL REVEAL ──────────────────────── (unchanged, but re-applied
   after dynamic content loads — see observeReveals() below) */
const revealObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      revealObs.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });

function observeReveals() {
  document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));
}

/* ── 5. ACTIVE NAV LINK ON SCROLL ──────────── (unchanged from before) */
const sections  = document.querySelectorAll('section[id]');
const navAnchors = document.querySelectorAll('.nav-links a');

const navObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      navAnchors.forEach(a => a.style.color = '');
      const active = document.querySelector(`.nav-links a[href="#${e.target.id}"]`);
      if (active) active.style.color = 'var(--cyan)';
    }
  });
}, { threshold: 0.45 });

sections.forEach(s => navObs.observe(s));


/* ════════════════════════════════════════════════════════════
   6. BACKEND INTEGRATION — Project 4
   ════════════════════════════════════════════════════════════

   This is the part that actually connects to the FastAPI backend.
   Pattern used everywhere below, matching the brief's I-P-O model:

     INPUT   -> fetch(url)                       (send the request)
     PROCESS -> await response, check response.ok (let the server work)
     OUTPUT  -> response.json(), then update DOM  (render the result)

   Every call is wrapped in try/catch/finally so a slow or dead
   backend never leaves the page blank — it falls back to the
   static content that's already hardcoded in the HTML.
*/

/** Small helper: GET an endpoint and return parsed JSON, or null on failure. */
async function fetchJSON(path) {
  try {
    const res = await fetch(API_BASE + path);
    if (!res.ok) {
      console.warn(`API request failed: ${path} -> ${res.status}`);
      return null;
    }
    return await res.json();
  } catch (err) {
    // Network error (server not running, CORS issue, offline, etc.)
    console.warn(`API unreachable for ${path}:`, err.message);
    return null;
  }
}

/** Escapes user-supplied text before inserting it as HTML.
    (Brief's security note: prefer textContent over innerHTML for
    user data — this is the innerHTML-safe equivalent when we DO
    need to build markup, by neutralizing angle brackets first.) */
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* ── HERO ── */
async function loadHero() {
  const hero = await fetchJSON("/api/hero");
  if (!hero) { startTyping(); return; }   // keep static fallback content, just start typing

  document.getElementById('heroName1').textContent = hero.name_line1 || "Muhammad";
  document.getElementById('heroName2').textContent = hero.name_line2 || "Abdul Kareem";
  document.getElementById('heroBadgeText').textContent = hero.badge_text || "Available for opportunities";
  document.getElementById('heroBio').textContent = hero.bio || "";

  if (Array.isArray(hero.roles) && hero.roles.length > 0) {
    roles = hero.roles;
  }

  const emailLink = document.getElementById('heroEmailLink');
  if (hero.email) {
    emailLink.href = `mailto:${hero.email}`;
    emailLink.textContent = `✉ ${hero.email}`;
  }

  const phoneLink = document.getElementById('heroPhoneLink');
  if (hero.phone) {
    phoneLink.href = `tel:${hero.phone.replace(/\s+/g, '')}`;
    phoneLink.textContent = `📞 ${hero.phone}`;
  }

  const linkedinLink = document.getElementById('heroLinkedinLink');
  if (hero.linkedin_url) {
    linkedinLink.href = hero.linkedin_url;
    linkedinLink.textContent = `🔗 ${hero.linkedin_label || "LinkedIn"}`;
  }

  startTyping();
}

/* ── ABOUT ── */
async function loadAbout() {
  const about = await fetchJSON("/api/about");
  if (!about) return; // keep static fallback

  if (Array.isArray(about.paragraphs) && about.paragraphs.length > 0) {
    const container = document.getElementById('aboutParagraphs');
    container.innerHTML = about.paragraphs.map(p => `<p>${escapeHtml(p)}</p>`).join("");
  }
  if (about.degree)   document.getElementById('aboutDegree').textContent = about.degree;
  if (about.semester) document.getElementById('aboutSemester').textContent = about.semester;
  if (about.cgpa)     document.getElementById('aboutCgpa').textContent = about.cgpa;
  if (about.location) document.getElementById('aboutLocation').textContent = about.location;

  if (about.photo_url) {
    const img = document.getElementById('aboutAvatarImg');
    const emoji = document.getElementById('aboutAvatarEmoji');
    img.src = API_BASE + about.photo_url;
    img.hidden = false;
    emoji.hidden = true;
  }
}

/* ── SKILLS ── */
async function loadSkills() {
  const skills = await fetchJSON("/api/skills");
  if (!skills || skills.length === 0) return; // keep static fallback

  const grid = document.getElementById('skillsGrid');
  grid.innerHTML = skills.map(s => `
    <article class="skill-card reveal">
      <div class="skill-card-icon" aria-hidden="true">${escapeHtml(s.icon || "💻")}</div>
      <h3>${escapeHtml(s.title)}</h3>
      <div class="skill-tags" role="list">
        ${(s.tags || []).map(t => `<span class="tag" role="listitem">${escapeHtml(t)}</span>`).join("")}
      </div>
    </article>
  `).join("");
}

/* ── EXPERIENCE ── */
async function loadExperience() {
  const items = await fetchJSON("/api/experience");
  if (!items || items.length === 0) return; // keep static fallback

  const list = document.getElementById('timelineList');
  list.innerHTML = items.map(item => `
    <article class="timeline-item reveal" role="listitem">
      <div class="timeline-meta">
        <span class="timeline-date">${escapeHtml(item.date_range)}</span>
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p class="timeline-org">${escapeHtml(item.organization)}</p>
      <ul aria-label="Details">
        ${(item.bullets || []).map(b => `<li>${escapeHtml(b)}</li>`).join("")}
      </ul>
      ${(item.tools && item.tools.length) ? `
        <div class="timeline-tools" aria-label="Technologies used">
          ${item.tools.map(t => `<span class="tool-tag">${escapeHtml(t)}</span>`).join("")}
        </div>` : ""}
    </article>
  `).join("");
}

/* ── PROJECTS ── */
async function loadProjects() {
  const projects = await fetchJSON("/api/projects");
  if (!projects || projects.length === 0) return; // keep static fallback

  const grid = document.getElementById('projectsGrid');
  grid.innerHTML = projects.map(p => `
    <article class="project-card reveal">
      <div class="project-header">
        <div class="project-icon" aria-hidden="true">${escapeHtml(p.icon || "💼")}</div>
        <div class="project-links">
          <a href="${escapeHtml(p.github_url || '#')}" aria-label="View ${escapeHtml(p.title)} on GitHub">GitHub ↗</a>
        </div>
      </div>
      <div>
        <div class="project-period">${escapeHtml(p.period)}</div>
        <h3>${escapeHtml(p.title)}</h3>
      </div>
      <p>${escapeHtml(p.description)}</p>
      <div class="skill-tags">
        ${(p.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("")}
      </div>
    </article>
  `).join("");
}

/* ── CONTACT INFO ── */
async function loadContactInfo() {
  const info = await fetchJSON("/api/contact-info");
  if (!info) return; // keep static fallback

  if (info.email) {
    document.getElementById('ciEmailValue').textContent = info.email;
  }
  if (info.phone) {
    document.getElementById('ciPhoneValue').textContent = info.phone;
  }
  if (info.location) {
    document.getElementById('ciLocationValue').textContent = info.location;
  }
  if (info.linkedin_label) {
    document.getElementById('ciLinkedinValue').textContent = info.linkedin_label;
  }
}

/* ── LOAD EVERYTHING ON PAGE LOAD ──
   Promise.all fires all six requests in PARALLEL rather than one
   after another — this is exactly the brief's anti-pattern fix
   ("await inside a for loop" -> use Promise.all() instead). */
async function loadAllContent() {
  await Promise.all([
    loadHero(),
    loadAbout(),
    loadSkills(),
    loadExperience(),
    loadProjects(),
    loadContactInfo(),
  ]);
  // Re-scan for .reveal elements now that dynamic content has replaced
  // the static placeholders, so the scroll-in animation still applies.
  observeReveals();
}

loadAllContent();


/* ════════════════════════════════════════════════════════════
   7. CONTACT FORM — now submits for real via POST /api/messages
   ════════════════════════════════════════════════════════════ */
const submitBtn = document.getElementById('submitBtn');
const formErrorBanner = document.getElementById('formErrorBanner');

function validate(id, errorId, check) {
  const field = document.getElementById(id);
  const error = document.getElementById(errorId);
  const valid = check(field.value.trim());
  field.classList.toggle('error', !valid);
  error.classList.toggle('visible', !valid);
  return valid;
}

submitBtn.addEventListener('click', async () => {
  formErrorBanner.hidden = true;

  const v1 = validate('fname',   'fnameError',   v => v.length > 0);
  const v2 = validate('lname',   'lnameError',   v => v.length > 0);
  const v3 = validate('email',   'emailError',   v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v));
  const v4 = validate('subject', 'subjectError', v => v.length > 0);
  const v5 = validate('message', 'messageError', v => v.length >= 20);

  if (!(v1 && v2 && v3 && v4 && v5)) return;  // stop here if invalid

  const payload = {
    first_name: document.getElementById('fname').value.trim(),
    last_name:  document.getElementById('lname').value.trim(),
    email:      document.getElementById('email').value.trim(),
    subject:    document.getElementById('subject').value.trim(),
    message:    document.getElementById('message').value.trim(),
  };

  submitBtn.disabled = true;
  submitBtn.textContent = 'Sending…';

  try {
    const res = await fetch(API_BASE + "/api/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      // Server responded, but rejected the request (e.g. validation error)
      const data = await res.json().catch(() => ({}));
      const msg = Array.isArray(data.detail)
        ? data.detail.map(d => d.msg).join(", ")
        : (data.detail || "Something went wrong. Please try again.");
      throw new Error(msg);
    }

    // Success
    document.getElementById('contactForm').style.display = 'none';
    document.getElementById('formSuccess').classList.add('visible');

  } catch (err) {
    // Network failure (server down) or validation failure from above
    formErrorBanner.textContent = "⚠ Couldn't send your message: " + err.message;
    formErrorBanner.hidden = false;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Send Message →';
  }
});

// Clear error on input
['fname','lname','email','subject','message'].forEach(id => {
  document.getElementById(id).addEventListener('input', () => {
    document.getElementById(id).classList.remove('error');
    document.getElementById(id + 'Error').classList.remove('visible');
  });
});
