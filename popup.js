document.getElementById('scrapeBtn').addEventListener('click', () => {
    const statusEl = document.getElementById('status');
    statusEl.textContent = "Scraping...";

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        if (!tab || !tab.url || !tab.url.includes("codeforces.com")) {
            statusEl.textContent = "❌ Not a Codeforces problem page.";
            return;
        }

        chrome.tabs.sendMessage(tab.id, { action: "scrape" }, (response) => {
            if (chrome.runtime.lastError) {
                statusEl.textContent = "❌ Couldn't reach page. Try reloading it.";
                return;
            }
            statusEl.textContent = "✅ Sent — check server.py console.";
        });
    });
});