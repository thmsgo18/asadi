function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function confirmerSuppression(userId, nomComplet) {
    if (confirm("⚠️ Confirmez-vous la suppression de " + nomComplet + " ?")) {
        fetch(SUPPRESSION_URL, {
            method: "POST",
            headers: {
                "X-CSRFToken": CSRF_TOKEN,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({ user_id: userId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const row = document.getElementById("user-row-" + userId);
                    if (row) row.remove();
                } else {
                    alert("Erreur : " + data.error || "Échec de la suppression.");
                }
            });
    }
}