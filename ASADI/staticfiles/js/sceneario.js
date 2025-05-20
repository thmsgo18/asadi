
function ouvrirScenario() {
    document.getElementById("scenarioModal").style.display = "block";
}

function fermerScenario() {
    document.getElementById("scenarioModal").style.display = "none";
}

// Ferme le modal si on clique en dehors
window.onclick = function(event) {
    const modal = document.getElementById("scenarioModal");
    if (event.target === modal) {
        modal.style.display = "none";
    }
}

