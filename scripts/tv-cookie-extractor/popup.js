const $ = (id) => document.getElementById(id);
const setStatus = (msg, cls = "") => {
  const el = $("status");
  el.textContent = msg;
  el.className = cls;
};

const SAMESITE_OUT = {
  no_restriction: "no_restriction",
  lax: "lax",
  strict: "strict",
  unspecified: "no_restriction"
};

async function getTvCookies() {
  const raw = await chrome.cookies.getAll({ domain: "tradingview.com" });
  return raw
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((c) => {
      const out = {
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        secure: !!c.secure,
        httpOnly: !!c.httpOnly,
        sameSite: SAMESITE_OUT[c.sameSite] || "no_restriction"
      };
      if (!c.session && typeof c.expirationDate === "number") {
        out.expirationDate = c.expirationDate;
      }
      return out;
    });
}

async function buildJSON() {
  try {
    const cookies = await getTvCookies();
    if (!cookies.length) {
      setStatus("No tradingview.com cookies found — log in first.", "err");
      return null;
    }
    setStatus(`Found ${cookies.length} cookie(s).`, "ok");
    return JSON.stringify(cookies, null, 2);
  } catch (e) {
    setStatus(`Error: ${e.message}`, "err");
    return null;
  }
}

$("copy").addEventListener("click", async () => {
  const json = await buildJSON();
  if (!json) return;
  try {
    await navigator.clipboard.writeText(json);
    setStatus(`Copied ${JSON.parse(json).length} cookie(s) to clipboard.`, "ok");
  } catch (e) {
    setStatus(`Clipboard failed: ${e.message}. Use "Show" and copy manually.`, "err");
  }
});

$("download").addEventListener("click", async () => {
  const json = await buildJSON();
  if (!json) return;
  const dataUrl = "data:application/json;charset=utf-8," + encodeURIComponent(json);
  await chrome.downloads.download({
    url: dataUrl,
    filename: `tradingview-cookies-${Date.now()}.json`,
    saveAs: true
  });
});

$("show").addEventListener("click", async () => {
  const ta = $("out");
  if (ta.style.display === "none") {
    const json = await buildJSON();
    if (!json) return;
    ta.value = json;
    ta.style.display = "block";
  } else {
    ta.style.display = "none";
  }
});

$("clear").addEventListener("click", () => {
  const ta = $("out");
  ta.value = "";
  ta.style.display = "none";
  setStatus("");
});
