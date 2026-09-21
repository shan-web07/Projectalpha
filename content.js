function scrapeProblem() {
    const timeLimitEl = document.querySelector('.time-limit');
    if (!timeLimitEl) {
        console.warn("CF Tester: couldn't find problem statement on this page.");
        alert("CF Tester: no problem statement detected here. Make sure you're on a problem page.");
        return;
    }
    const timeLimit = timeLimitEl.innerText;

const problemStatement =
    document.querySelector(".problem-statement")?.innerText || "";

const inputs = Array.from(
    document.querySelectorAll('.sample-test .input pre')
).map(el => el.innerText);

const outputs = Array.from(
    document.querySelectorAll('.sample-test .output pre')
).map(el => el.innerText);

const userCode =
    document.getElementById('sourceCodeTextarea')?.value || "";

    if (!userCode) {
        console.warn("CF Tester: no code found in the inline editor. Make sure the submit form is open and has code in it.");
    }
    if (inputs.length === 0) {
        console.warn("CF Tester: no sample inputs found on this page.");
    }

    fetch('http://localhost:8080/stress-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
    timeLimit,
    problemStatement,
    inputs,
    outputs,
    userCode })
    })
    .then(res => {
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        return res.json();
    })
    .then(data => {
        console.log("✅ CF Tester: sent to local server", data);
    })
    .catch(err => {
        console.error("❌ CF Tester: failed to reach local server. Is server.py running on port 8080?", err);
        alert("CF Tester: couldn't reach the local server. Make sure server.py is running.");
    });
}

// Triggered by popup.js when the user clicks the extension icon
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "scrape") {
        scrapeProblem();
        sendResponse({ status: "started" });
    }
    return true;
});