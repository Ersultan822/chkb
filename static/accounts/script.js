(() => {
  const CART_KEY = "tulga_cart";
  const CHOSEN_KEY = "tulga_chosen_product";

  const $ = (id) => document.getElementById(id);

  function parsePriceKZT(text) {
    return Number(String(text || "0").replace(/[^\d]/g, "")) || 0;
  }

  function getCart() {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  }

  function setCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  }

  function setChosen(name) {
    localStorage.setItem(CHOSEN_KEY, name || "");
    const el = $("chosenProduct");
    if (el) el.textContent = name || "— таңдалмаған";
  }

  function getChosen() {
    return localStorage.getItem(CHOSEN_KEY) || "";
  }

  function getCsrfToken() {
    const name = "csrftoken=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(";");
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i].trim();
      if (c.indexOf(name) === 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }

  function bindUrgency() {
    const r = $("urgency");
    const v = $("urgencyVal");
    if (!r || !v) return;
    const sync = () => v.textContent = r.value;
    r.addEventListener("input", sync);
    sync();
  }

  function readSupportForm() {
    const form = $("supportForm");
    if (!form) return null;
    const use = form.querySelector("input[name='use']:checked")?.value || "study";
    const budget = form.querySelector("select[name='budget']")?.value || "0-220";
    const screen = form.querySelector("input[name='screen']:checked")?.value || "any";
    const req = Array.from(form.querySelectorAll("input[name='req']:checked")).map((x) => x.value);
    return { use, budget, screen, req };
  }

  function recommend(sel) {
    const products = [
      { name: "TULGA Pro 15", price: 189990, tags: ["study"], screen: "15", caps: ["ssd512", "ram16", "portable"] },
      { name: "TULGA Gamer 16", price: 499990, tags: ["gaming"], screen: "16", caps: ["ssd1tb", "ram16", "gpuRTX"] },
      { name: "TULGA Station PC", price: 549990, tags: ["work"], screen: "any", caps: ["ssd1tb", "ram32", "gpuRTX"] },
    ];

    const maxBudget =
      sel.budget === "0-220" ? 220000 :
      sel.budget === "220-450" ? 450000 : Infinity;

    let best = null;
    let bestScore = -999;

    for (const p of products) {
      let score = 0;
      if (sel.use === "study" && p.tags.includes("study")) score += 6;
      if (sel.use === "gaming" && p.tags.includes("gaming")) score += 6;
      if (sel.use === "work" && p.tags.includes("work")) score += 6;
      if (p.price <= maxBudget) score += 3; else score -= 6;
      if (sel.screen !== "any") score += (p.screen === sel.screen ? 2 : -1);
      for (const r of sel.req) score += p.caps.includes(r) ? 1 : -1;
      if (score > bestScore) {
        bestScore = score;
        best = p;
      }
    }

    return { best, score: bestScore };
  }

  function bindSupport() {
    const run = $("supportRun");
    const reset = $("supportReset");
    const note = $("supportNote");
    const out = $("supportResult");

    if (reset && out) {
      reset.addEventListener("click", () => {
        if (note) note.textContent = "";
        out.textContent = "Талаптарды таңдаңыз да “Ұсыну” басыңыз.";
      });
    }

    if (!run) return;

    run.addEventListener("click", () => {
      const sel = readSupportForm();
      if (!sel) return;

      const { best, score } = recommend(sel);

      if (!best) {
        if (note) note.textContent = "Ұсыныс табылмады.";
        if (out) out.textContent = "—";
        return;
      }

      if (note) note.textContent = "✅ Ұсыныс дайын.";
      if (out) {
        out.innerHTML =
          `<b>${best.name}</b><br>` +
          `<span class="muted small">Бағасы: ${best.price} ₸ • Score: ${score}</span><br><br>` +
          `<span class="muted">Себебі: мақсат/бюджет/талаптарға ең жақын.</span>`;
      }

      setChosen(best.name);
    });
  }

  function escapePdfText(s) {
    return String(s).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
  }

  function buildSimplePdf(lines) {
    const ops = [];
    let y = 760;

    for (const line of lines) {
      ops.push(`1 0 0 1 50 ${y} Tm (${escapePdfText(line)}) Tj`);
      y -= 18;
    }

    const stream = `BT\n/F1 12 Tf\n${ops.join("\n")}\nET\n`;

    const objs = [];
    const obj = (n, body) => objs[n] = body;

    obj(1, `<< /Type /Catalog /Pages 2 0 R >>`);
    obj(2, `<< /Type /Pages /Kids [3 0 R] /Count 1 >>`);
    obj(3, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>`);
    obj(4, `<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>`);
    obj(5, `<< /Length ${stream.length} >>\nstream\n${stream}endstream`);

    let pdf = `%PDF-1.4\n`;
    const offsets = [0];

    for (let i = 1; i <= 5; i++) {
      offsets[i] = pdf.length;
      pdf += `${i} 0 obj\n${objs[i]}\nendobj\n`;
    }

    const xrefStart = pdf.length;
    pdf += `xref\n0 6\n0000000000 65535 f \n`;

    for (let i = 1; i <= 5; i++) {
      pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
    }

    pdf += `trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF`;

    return new Blob([pdf], { type: "application/pdf" });
  }

  function downloadBlob(blob, filename) {
    const a = document.createElement("a");
    const url = URL.createObjectURL(blob);
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 600);
  }

  function bindPdf() {
    const btn = $("downloadBtn");
    const clear = $("clearDl");
    const note = $("dlNote");
    const form = $("downloadForm");

    if (clear && form) {
      clear.addEventListener("click", () => {
        form.querySelectorAll("input[type='checkbox']").forEach((c) => c.checked = false);
        if (note) note.textContent = "";
      });
    }

    if (!btn || !form) return;

    btn.addEventListener("click", () => {
      const checked = Array.from(form.querySelectorAll("input[name='dl']:checked")).map((x) => x.value);

      if (!checked.length) {
        if (note) note.textContent = "Кемінде 1 пункт таңдаңыз.";
        return;
      }

      const chosen = getChosen() || "TULGA (таңдалмаған)";
      const dateStr = new Date().toLocaleString();

      checked.forEach((type) => {
        const isWarranty = type === "warranty";
        const title = isWarranty ? "GARANTIYA (DEMO)" : "NUSQAULYQ / INSTRUKCIYA (DEMO)";
        const lines = [
          "TULGA STORE",
          title,
          "------------------------------",
          `Tovar: ${chosen}`,
          `Kuni: ${dateStr}`,
          "",
          isWarranty ? "Bul demo garantiya." : "Bul demo instrukciya.",
          "",
          "Kontakt: +7 (777) 777-77-77",
        ];

        const blob = buildSimplePdf(lines);
        const safe = chosen.replace(/[^\w\d\-_. ]+/g, "").replace(/\s+/g, "_");
        const fname = isWarranty ? `garantiya_${safe}.pdf` : `nuskaulyk_${safe}.pdf`;
        downloadBlob(blob, fname);
      });

      if (note) note.textContent = "✅ Файл(дар) жүктелді.";
    });
  }

  function bindPick() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".pickProduct");
      if (!btn) return;

      const name = btn.dataset.name || btn.closest(".product")?.querySelector(".ptitle")?.innerText || "";
      if (name) setChosen(name);

      const dl = $("dlNote");
      if (dl && name) dl.textContent = `Таңдалды: ${name}`;
    });

    const saved = getChosen();
    if (saved) setChosen(saved);
  }

  function bindOrder() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".orderBtn");
      if (!btn) return;

      e.preventDefault();

      const isLoggedIn = document.body.dataset.auth === "true";
      if (!isLoggedIn) {
        window.location.href = "/login/";
        return;
      }

      const card = btn.closest(".product");
      const name = btn.dataset.product || card?.querySelector(".ptitle")?.innerText?.trim() || "Тауар";
      const priceText = card?.querySelector("strong")?.innerText || "0";
      const price = parsePriceKZT(priceText);

      const cart = getCart();
      cart.push({ name, price });
      setCart(cart);

      window.location.href = "/cart/";
    });
  }

  // =========================
  // CHAT + VOICE ASSISTANT
  // =========================

  function bindAssistant() {
    const chatToggle = $("chatToggle");
    const chatBox = $("chatBox");
    const chatClose = $("chatClose");
    const chatSend = $("chatSend");
    const chatInput = $("chatInput");
    const chatBody = $("chatBody");
    const voiceBtn = $("voiceBtn");
    const chatChips = document.querySelectorAll(".tulga-chat-chip");

    function addChatMessage(text, type) {
      if (!chatBody) return;

      const wrapper = document.createElement("div");
      wrapper.className = "tulga-chat-msg " + type;

      const bubble = document.createElement("div");
      bubble.className = "tulga-chat-bubble";
      bubble.innerText = text;

      wrapper.appendChild(bubble);
      chatBody.appendChild(wrapper);
      chatBody.scrollTop = chatBody.scrollHeight;
    }

    function speakText(text) {
      if (!("speechSynthesis" in window)) return;

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "kk-KZ";
      utterance.rate = 1;
      utterance.pitch = 1;

      window.speechSynthesis.speak(utterance);
    }

    async function sendChatMessage(customMessage = null, fromVoice = false) {
      const message = customMessage !== null ? customMessage : (chatInput ? chatInput.value.trim() : "");

      if (!message) return;

      // ҚОЛМЕН ЖАЗҒАНДА ҒАНА user message көрсетеміз
      if (!fromVoice) {
        addChatMessage(message, "user");
      }

      if (chatInput && customMessage === null) {
        chatInput.value = "";
      }

      try {
        const response = await fetch(`/assistant/?message=${encodeURIComponent(message)}`);
        const data = await response.json();

        if (data.text) {
          addChatMessage(data.text, "bot");

          if (fromVoice) {
            speakText(data.text);
          }
        }

        if (data.action === "redirect" && data.url) {
          setTimeout(() => {
            window.location.href = data.url;
          }, 800);
          return;
        }

        if (data.action === "add_to_cart" && data.slug) {
          const form = document.createElement("form");
          form.method = "POST";
          form.action = `/cart/add/${data.slug}/`;

          const csrfInput = document.createElement("input");
          csrfInput.type = "hidden";
          csrfInput.name = "csrfmiddlewaretoken";
          csrfInput.value = getCsrfToken();

          form.appendChild(csrfInput);
          document.body.appendChild(form);
          form.submit();
          return;
        }
      } catch (error) {
        const errorText = "Қате шықты. Қайтадан көріңіз.";
        addChatMessage(errorText, "bot");

        if (fromVoice) {
          speakText(errorText);
        }
      }
    }

    if (chatToggle && chatBox) {
      chatToggle.addEventListener("click", function () {
        chatBox.classList.toggle("open");
      });
    }

    if (chatClose && chatBox) {
      chatClose.addEventListener("click", function () {
        chatBox.classList.remove("open");
      });
    }

    if (chatSend) {
      chatSend.addEventListener("click", function () {
        sendChatMessage();
      });
    }

    if (chatInput) {
      chatInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          sendChatMessage();
        }
      });
    }

    if (chatChips.length) {
      chatChips.forEach(function (chip) {
        chip.addEventListener("click", function () {
          sendChatMessage(chip.dataset.msg, false);
        });
      });
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      if (voiceBtn) {
        voiceBtn.style.display = "none";
      }
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "kk-KZ";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    if (voiceBtn) {
      voiceBtn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();

        try {
          voiceBtn.classList.add("listening");
          speakText("Тыңдап тұрмын");
          recognition.start();
        } catch (err) {
          console.log(err);
        }
      });
    }

    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript.trim();

      // Дауыс мәтінін input-қа салмаймыз
      if (chatInput) {
        chatInput.value = "";
      }

      // Чатқа user message болып шықпайды
      sendChatMessage(transcript, true);
    };

    recognition.onerror = function (event) {
      if (voiceBtn) {
        voiceBtn.classList.remove("listening");
      }

      let msg = "Дауыс танылмады.";

      if (event.error === "not-allowed") {
        msg = "Микрофонға рұқсат берілмеген.";
      } else if (event.error === "no-speech") {
        msg = "Ештеңе естілмеді.";
      } else if (event.error === "audio-capture") {
        msg = "Микрофон табылмады.";
      }

      addChatMessage(msg, "bot");
      speakText(msg);
    };

    recognition.onend = function () {
      if (voiceBtn) {
        voiceBtn.classList.remove("listening");
      }
    };
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindUrgency();
    bindSupport();
    bindPdf();
    bindPick();
    bindOrder();
    bindAssistant();
  });
})();
function initTheme() {
  const btn = document.getElementById("themeToggle");

  const saved = localStorage.getItem("theme");

  if (saved === "dark") {
    document.body.classList.add("dark-mode");
    if (btn) btn.innerText = "☀️";
  }

  if (!btn) return;

  btn.onclick = () => {
    const dark = document.body.classList.toggle("dark-mode");

    if (dark) {
      localStorage.setItem("theme", "dark");
      btn.innerText = "☀️";
    } else {
      localStorage.setItem("theme", "light");
      btn.innerText = "🌙";
    }
  };
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
});