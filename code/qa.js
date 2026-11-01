// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8797; set PORT to change).
const { chromium } = require("playwright");
// Leaflet from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here.
const LEAF = process.env.LEAFLET_DIST || "/dev/shm/piracy/npm/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8797) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    await p.click('#eraRow .btn:nth-child(5)'); await p.waitForTimeout(900); await shot("#atlas", "era_medieval");
    await p.click('#viewRow [data-v="hex"]'); await p.click('#eraRow .btn:nth-child(2)'); await p.waitForTimeout(900); await shot("#atlas", "hex_all");
    await p.click('#viewRow [data-v="dots"]'); await p.click('#colRow [data-c="kind"]'); await p.click("#focusRow .btn:nth-child(4)"); await p.waitForTimeout(1200); await shot("#atlas", "flanders_kind");
    await p.click('#colRow [data-c="era"]'); await p.click('#viewRow [data-v="both"]'); await p.click("#focusRow .btn:nth-child(2)"); await p.click("#play"); await p.waitForTimeout(30000); await shot("#atlas", "playing");
    await p.click("#play"); await p.click('#eraRow .btn:nth-child(2)');
    await p.click(".lyrBtn"); await p.check('.lyrPanel [data-k="topReg"]'); await p.check('.lyrPanel [data-k="centre"]'); await p.waitForTimeout(1500); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
    await p.click("#focusRow .btn:nth-child(3)"); await p.waitForTimeout(1200); await shot("#atlas", "europe_regions");
    await p.click(".lyrBtn"); await p.uncheck('.lyrPanel [data-k="topReg"]'); await p.uncheck('.lyrPanel [data-k="centre"]'); await p.check('.lyrPanel [data-k="cas"]'); await p.click(".lyrBtn"); await p.waitForTimeout(1500); await shot("#atlas", "casualties");
    await p.click(".lyrBtn"); await p.uncheck('.lyrPanel [data-k="cas"]'); await p.click(".lyrBtn");
    await p.selectOption("#warSel", { index: 3 }); await p.waitForTimeout(1500); await shot("#atlas", "war_acw");
    await p.selectOption("#warSel", { index: 0 }); await p.waitForTimeout(500);
    await p.fill("#q", "Waterloo"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(1800); await shot("#atlas", "search_waterloo");
    await p.fill("#q", "Hundred Years"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(1800); await shot("#atlas", "search_war");
    await p.selectOption("#warSel", { index: 0 });
    for (const c of ["centChart", "centreChart", "places", "warChart", "contChart", "slChart", "kindChart"]) await shot("#" + c, c);
    await p.click('#cMode [data-m="log"]'); await p.waitForTimeout(400); await shot("#centChart", "centChart_log");
    await p.click('#cMode [data-m="share"]'); await p.waitForTimeout(400); await shot("#centChart", "centChart_share");
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#centChart", "dark_cent");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
