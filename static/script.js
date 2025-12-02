const pwdInput = document.getElementById("pwd");
const meterBar = document.getElementById("meter-bar");
const labelEl = document.getElementById("label");
const entropyEl = document.getElementById("entropy");
const issuesEl = document.getElementById("issues");
const suggestList = document.getElementById("suggest-list");

let pending = null;

async function checkPassword(pwd) {
  // call backend API
  try {
    const res = await fetch("/api/check", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password: pwd})
    });
    if (!res.ok) throw new Error("Network response not ok");
    return await res.json();
  } catch (e) {
    console.error(e);
    return null;
  }
}

function updateUI(result) {
  if (!result) return;
  const score = result.score;
  meterBar.style.width = score + "%";
  // color by score
  if (score < 35) {
    meterBar.style.filter = "hue-rotate(0deg) saturate(120%)";
  } else if (score < 60) {
    meterBar.style.filter = "hue-rotate(40deg) saturate(120%)";
  } else if (score < 80) {
    meterBar.style.filter = "hue-rotate(100deg) saturate(120%)";
  } else {
    meterBar.style.filter = "hue-rotate(140deg) saturate(120%)";
  }

  labelEl.textContent = result.label;
  entropyEl.textContent = "Entropy: " + result.entropy;

  // issues
  if (result.issues && result.issues.length > 0) {
    issuesEl.style.display = "block";
    issuesEl.innerHTML = "<strong>Detected issues:</strong><ul>" + result.issues.map(i => "<li>"+i+"</li>").join("") + "</ul>";
  } else {
    issuesEl.style.display = "none";
    issuesEl.innerHTML = "";
  }

  // suggestions
  suggestList.innerHTML = "";
  if (result.suggestions && result.suggestions.length > 0) {
    result.suggestions.forEach(s => {
      const li = document.createElement("li");
      li.textContent = s;
      suggestList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "No suggestions — your password looks good!";
    suggestList.appendChild(li);
  }
}

// debounce input requests
let timer = null;
pwdInput.addEventListener("input", () => {
  clearTimeout(timer);
  const value = pwdInput.value;
  // quick client-side UX: set meter proportional to length while waiting
  const quick = Math.min(40, value.length * 3);
  meterBar.style.width = quick + "%";
  labelEl.textContent = "Checking...";
  entropyEl.textContent = "Entropy: --";
  issuesEl.style.display = "none";
  suggestList.innerHTML = "";

  timer = setTimeout(async () => {
    const res = await checkPassword(value);
    if (res) updateUI(res);
  }, 300);
});
