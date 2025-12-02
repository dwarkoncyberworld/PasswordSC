from flask import Flask, render_template, request, jsonify
import math
import re

app = Flask(__name__)

COMMON_WORDS = {
    "password","123456","12345678","qwerty","abc123","letmein","welcome",
    "iloveyou","admin","login","princess","dragon","passw0rd"
}

def estimate_entropy(password: str) -> float:
    """
    Rough entropy estimate based on character sets used and length:
    - lowercase (26), uppercase (26), digits (10), symbols (~32)
    Then entropy_per_char = log2(pool_size). Total entropy = len * entropy_per_char.
    """
    pool = 0
    if re.search(r"[a-z]", password): pool += 26
    if re.search(r"[A-Z]", password): pool += 26
    if re.search(r"[0-9]", password): pool += 10
    if re.search(r"[^\w]", password): pool += 32  # rough estimate for symbols
    if pool == 0:
        return 0.0
    entropy_per_char = math.log2(pool)
    return round(entropy_per_char * len(password), 2)

def detect_patterns(password: str) -> list:
    issues = []
    # repeated character sequences
    if re.search(r"(.)\1\1", password):
        issues.append("Contains repeated characters (e.g. aaa).")
    # sequential characters (abc, 123, cba, 321)
    seq_found = False
    s = password.lower()
    for i in range(len(s)-2):
        a,b,c = ord(s[i]), ord(s[i+1]), ord(s[i+2])
        if b-a == 1 and c-b == 1:
            seq_found = True
        if a-b == 1 and b-c == 1:
            seq_found = True
    if seq_found:
        issues.append("Contains sequential characters (e.g. abc or 123).")
    # common words/dictionary
    for w in COMMON_WORDS:
        if w in s:
            issues.append(f"Contains common word or pattern: '{w}'.")
            break
    # short length
    if len(password) < 8:
        issues.append("Password length is less than 8 characters.")
    return issues

def score_password(password: str) -> dict:
    if password == "":
        return {"score": 0, "label": "Empty", "entropy": 0.0, "issues": [], "suggestions": []}
    entropy = estimate_entropy(password)
    issues = detect_patterns(password)

    # Base score from entropy
    # We'll map entropy to a 0-100 scale:
    # 0-28 -> weak, 28-50 -> medium, 50-75 strong, 75+ very strong
    if entropy < 28:
        score = int(max(5, entropy / 28 * 40))  # up to 40
        label = "Weak"
    elif entropy < 50:
        score = int(40 + (entropy-28) / (50-28) * 20)  # 40-60
        label = "Medium"
    elif entropy < 75:
        score = int(60 + (entropy-50) / (75-50) * 25)  # 60-85
        label = "Strong"
    else:
        score = int(min(100, 85 + (entropy-75) / 30 * 15))  # up to 100
        label = "Very Strong"

    # Penalties for obvious issues
    penalty = 0
    if any("common" in i for i in issues):
        penalty += 25
    if any("repeated" in i for i in issues):
        penalty += 10
    if any("sequential" in i for i in issues):
        penalty += 10
    if len(password) < 8:
        penalty += 20

    score = max(0, score - penalty)
    # Re-evaluate label by final score
    if score < 35:
        label = "Weak"
    elif score < 60:
        label = "Medium"
    elif score < 80:
        label = "Strong"
    else:
        label = "Very Strong"

    suggestions = []
    if len(password) < 12:
        suggestions.append("Increase length to at least 12 characters — longer passwords are stronger.")
    if not re.search(r"[A-Z]", password):
        suggestions.append("Add uppercase letters.")
    if not re.search(r"[a-z]", password):
        suggestions.append("Add lowercase letters.")
    if not re.search(r"[0-9]", password):
        suggestions.append("Add digits (0-9).")
    if not re.search(r"[^\w]", password):
        suggestions.append("Add symbols (e.g. !@#$%^&*).")
    if any("common" in i for i in issues):
        suggestions.append("Avoid using common words, dictionary words, or predictable patterns.")
    if any("sequential" in i for i in issues) or any("repeated" in i for i in issues):
        suggestions.append("Avoid long repeated or sequential characters (e.g. 1111, abcd).")
    if score < 40 and "Use a password manager" not in suggestions:
        suggestions.append("Use a reputable password manager to generate and store strong unique passwords.")

    return {
        "score": score,
        "label": label,
        "entropy": entropy,
        "issues": issues,
        "suggestions": suggestions
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.get_json() or {}
    password = data.get("password", "")
    # IMPORTANT: Do NOT log or store real passwords in production. This demo processes in memory only.
    result = score_password(password)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
