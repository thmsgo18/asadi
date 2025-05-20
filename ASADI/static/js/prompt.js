// désactive le form et affiche l'overlay
function showLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    const sendBtn = document.getElementById('send-prompt');
    if (overlay) overlay.style.display = 'flex';
    if (sendBtn) sendBtn.disabled = true;
}
  
  // (optionnel) bind automatique si vous voulez éviter l’inline
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form[action*="?prompt_id"]');
    if (form) {
      form.addEventListener('submit', showLoadingOverlay);
    }
});
  
//fonction pour le pop Up profil
function afficherProfil() {
    document.getElementById("profilModal").style.display = "block";
}
  
function fermerProfil() {
    document.getElementById("profilModal").style.display = "none";
    const url = new URL(window.location);
    url.searchParams.delete("open");
    url.searchParams.delete("msg");
    window.history.replaceState({}, document.title, url.toString());
}
  
// Fermer si clic en dehors de la fenêtre
window.onclick = function(event) {
    const modal = document.getElementById("profilModal");
    if (event.target === modal) {
        fermerProfil()
    }
}
  
  
  
document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById("myModal");
    var btn = document.querySelector(".filter-btn");
    var span = document.querySelector(".close");
  
    btn.addEventListener("click", function() {
          modal.style.display = "block";
    });
  
    span.addEventListener("click", function() {
        modal.style.display = "none";
    });
  
    window.addEventListener("click", function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});
  

window.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const msg = params.get("msg");
    const open = params.get("open");
  
    if (open === "profil") {
        afficherProfil();
        const messageBox = document.getElementById("profil-message");
        if (messageBox && msg) {
  
            let text = "";
            let type = "error"; // par défaut
  
            switch (msg) {
                case "success":
                    text = "Mot de passe modifié avec succès.";
                    type = "success";
                    break;
                case "wrong_old":
                    text = "Mot de passe actuel incorrect.";
                    break;
                case "nomatch":
                    text = "Les mots de passe ne correspondent pas.";
                    break;
                case "error":
                    text = "Une erreur est survenue. Vérifie les champs.";
                    break;
            }
  
            messageBox.textContent = decodeURIComponent(msg);
            messageBox.className = "profil-message " + (msg.includes("succès") ? "success" : "error");
            /*messageBox.textContent = text;
            messageBox.className = "profil-message " + type;*/
        }
    }
});
  
  
window.addEventListener('load', function () {
    const chatScroll = document.getElementById('chat-scroll');
    if (chatScroll) {
        chatScroll.scrollTop = chatScroll.scrollHeight;
    }
});
  
  //Fonction pour afficher formulaire de mot de passe
function changementPassword() {
    const section = document.getElementById("passwordChangeSection");
    section.style.display = section.style.display === "none" ? "block" : "none";
}
  
  //gestion de la barre de niveau
function setNiveau(valeur, max) {
    const barre = document.getElementById('progress');
    const barre_wrapper = document.getElementById('progress_wrapper')
    const pourcentage = (valeur / max) * 100;
  
    if (pourcentage > 60) {
        barre.style.backgroundColor = '#09f6ed';
        barre_wrapper.style.backgroundColor = '#87ccc4';
    } else if (pourcentage > 30) {
        barre.style.backgroundColor = '#FFB347';
        barre_wrapper.style.backgroundColor = '#d1a879';
    } else {
        barre.style.backgroundColor = '#D94352';
        barre_wrapper.style.backgroundColor = '#c8949b';
    }
}
  
if (window.utilisateurNiveau) {
    setNiveau(window.utilisateurNiveau.valeur, window.utilisateurNiveau.max);
}
  
  //pop-up information quiz
  
function ouvrirQuizInfos(titre, dateCreation, nbQuestions) {
    document.getElementById('quiz-titre').textContent = "Quiz sur " + titre;
    document.getElementById('quiz-titre-info').textContent = titre;
    document.getElementById('quiz-date-info').textContent = dateCreation;
    document.getElementById('quiz-nb-questions').textContent = nbQuestions;
  
    document.getElementById('quizModal').style.display = 'block';
}
  
function fermerQuiz() {
    document.getElementById('quizModal').style.display = 'none';
}
  
function ouvrirScenario(titre, contexte,nbQuestions) {
    document.getElementById('scenario-titre').textContent = "Scenario sur " + titre;
    document.getElementById('scenario-contexte').textContent = contexte;
    document.getElementById('scenario-nb-questions').textContent = nbQuestions;
  
    document.getElementById('scenarioModal').style.display = 'block';
}
  
function fermerScenario() {
    document.getElementById('scenarioModal').style.display = 'none';
}
  
  
window.onload = function() {
    // Vérifie si le feedback global existe
    if (document.getElementById('feedback-global')) {
        // Fait défiler la page jusqu'à l'élément avec l'ID "feedback-global"
        document.getElementById('feedback-global').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}
