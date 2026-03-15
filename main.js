/* ═══════════════════════════════════════════════════════════
   STEMPath — main.js
   Handles: dark mode, card filtering/search, match bar animation,
   compare toggle, checklist interactions, debounced search.
   ═══════════════════════════════════════════════════════════ */

"use strict";

/* ── Dark Mode ────────────────────────────────────────────── */
(function initDarkMode() {
  const toggle  = document.getElementById("darkModeToggle");
  const icon    = document.getElementById("darkIcon");
  const htmlEl  = document.documentElement;

  const saved = localStorage.getItem("stempath-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = saved === "dark" || (!saved && prefersDark);

  applyTheme(isDark);

  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = htmlEl.getAttribute("data-bs-theme") === "dark";
      applyTheme(!current);
      localStorage.setItem("stempath-theme", !current ? "dark" : "light");
    });
  }

  function applyTheme(dark) {
    htmlEl.setAttribute("data-bs-theme", dark ? "dark" : "light");
    if (icon) {
      icon.classList.toggle("fa-moon", !dark);
      icon.classList.toggle("fa-sun", dark);
    }
    if (toggle) toggle.setAttribute("aria-pressed", String(dark));
  }
})();

/* ── Animate Match Bars ─────────────────────────────────── */
(function animateMatchBars() {
  const bars = document.querySelectorAll(".match-bar-fill[data-score]");
  if (!bars.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el    = entry.target;
        const score = parseInt(el.dataset.score, 10);
        // Small delay then animate
        setTimeout(() => { el.style.width = score + "%"; }, 100);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.1 });

  bars.forEach(bar => {
    bar.style.width = "0%";
    observer.observe(bar);
  });
})();

/* ── Career Card Filtering & Search (Explore / Recommend) ── */
(function initCardFilter() {
  const searchInput  = document.getElementById("careerSearch");
  const filterChips  = document.querySelectorAll(".filter-chip[data-tag]");
  const clearBtn     = document.getElementById("clearFilters");
  const cardsWrap    = document.getElementById("careersGrid");
  const noResults    = document.getElementById("noResults");

  if (!cardsWrap) return;

  const cards = Array.from(cardsWrap.querySelectorAll("[data-tags]"));
  let activeTag = null;
  let searchVal = "";

  function updateCards() {
    let visible = 0;
    cards.forEach(card => {
      const tags    = (card.dataset.tags || "").toLowerCase();
      const title   = (card.dataset.title || "").toLowerCase();
      const skills  = (card.dataset.skills || "").toLowerCase();
      const haystack = `${tags} ${title} ${skills}`;

      const tagMatch  = !activeTag || tags.includes(activeTag);
      const textMatch = !searchVal || haystack.includes(searchVal);
      const show = tagMatch && textMatch;

      card.style.display = show ? "" : "none";
      if (show) visible++;
    });

    if (noResults) noResults.style.display = visible === 0 ? "" : "none";
  }

  // Filter chips
  filterChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const tag = chip.dataset.tag;
      if (activeTag === tag) {
        activeTag = null;
        chip.classList.remove("active");
        chip.setAttribute("aria-pressed", "false");
      } else {
        filterChips.forEach(c => {
          c.classList.remove("active");
          c.setAttribute("aria-pressed", "false");
        });
        activeTag = tag;
        chip.classList.add("active");
        chip.setAttribute("aria-pressed", "true");
      }
      updateCards();
    });
  });

  // Clear all
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      activeTag = null;
      searchVal = "";
      filterChips.forEach(c => {
        c.classList.remove("active");
        c.setAttribute("aria-pressed", "false");
      });
      if (searchInput) searchInput.value = "";
      updateCards();
    });
  }

  // Debounced search
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        searchVal = searchInput.value.trim().toLowerCase();
        updateCards();
      }, 200);
    });
  }
})();

/* ── Roadmap Checklist ──────────────────────────────────── */
(function initChecklist() {
  const items = document.querySelectorAll(".checklist li");
  if (!items.length) return;

  items.forEach(item => {
    item.addEventListener("click", () => {
      item.classList.toggle("done");
      const circle = item.querySelector(".check-circle");
      if (circle) {
        if (item.classList.contains("done")) {
          circle.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i>';
          item.setAttribute("aria-checked", "true");
        } else {
          circle.innerHTML = "";
          item.setAttribute("aria-checked", "false");
        }
      }
    });

    item.setAttribute("role", "checkbox");
    item.setAttribute("aria-checked", "false");
    item.setAttribute("tabindex", "0");

    item.addEventListener("keydown", e => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        item.click();
      }
    });
  });
})();

/* ── Quiz: Select All / Clear ───────────────────────────── */
(function initQuizHelpers() {
  document.querySelectorAll("[data-select-group]").forEach(btn => {
    const action = btn.dataset.selectGroup;
    const group  = btn.closest(".quiz-section");
    if (!group) return;

    btn.addEventListener("click", () => {
      group.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = action === "all";
      });
    });
  });
})();

/* ── Tooltip init (Bootstrap) ───────────────────────────── */
(function initTooltips() {
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
})();

/* ── Smooth anchor scrolling for detail page nav ─────────── */
(function initAnchorNav() {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener("click", e => {
      const target = document.querySelector(link.getAttribute("href"));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        target.focus({ preventScroll: true });
      }
    });
  });
})();
