// Gestionnaires d'événements ASADI
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du niveau utilisateur depuis l'attribut data-
    var userNiveau = document.getElementById('user-niveau-data');
    if (userNiveau) {
        window.utilisateurNiveau = {
            "valeur": parseInt(userNiveau.getAttribute('data-niveau')),
            "max": 20
        };
    }
    
    // Initialiser la barre de progression
    var progressBar = document.getElementById('progress');
    if (progressBar) {
        var niveau = parseInt(progressBar.getAttribute('data-niveau')) || 0;
        var pourcentage = Math.min(100, niveau * 100 / 20);
        progressBar.style.width = pourcentage + '%';
    }

    // Boutons de navigation simples
    document.querySelectorAll('.nav-button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            window.location.href = this.getAttribute('data-url');
        });
    });

    // Boutons qui demandent confirmation
    document.querySelectorAll('.restart-button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (confirm('Relancer ce quiz ?')) {
                window.location.href = this.getAttribute('data-url');
            }
        });
    });

    // Affichage info quiz
    document.querySelectorAll('.quiz-info').forEach(function(link) {
        link.addEventListener('click', function() {
            ouvrirQuizInfos(
                this.getAttribute('data-titre'),
                this.getAttribute('data-date'),
                this.getAttribute('data-count')
            );
        });
    });

    // Affichage info scénario
    document.querySelectorAll('.scenario-info').forEach(function(link) {
        link.addEventListener('click', function() {
            ouvrirScenario(
                this.getAttribute('data-titre'),
                this.getAttribute('data-contexte'),
                this.getAttribute('data-count')
            );
        });
    });

    // Toggle workspace radio deselection in popup and update prompt form action
    const promptForm = document.getElementById('prompt-form');
    let lastChecked = null;
    if (promptForm) {
        // compute base action without workspace param
        const urlObj = new URL(promptForm.action, window.location.href);
        urlObj.searchParams.delete('workspace');
        const baseAction = urlObj.pathname + urlObj.search;
        document.querySelectorAll('#myModal input[name="workspace"]').forEach(function(radio) {
            radio.addEventListener('click', function() {
                if (this === lastChecked) {
                    this.checked = false;
                    lastChecked = null;
                } else {
                    lastChecked = this;
                }
                // update prompt form action
                if (this.checked) {
                    promptForm.action = baseAction + '&workspace=' + encodeURIComponent(this.value);
                } else {
                    promptForm.action = baseAction;
                }
            });
        });
    }
});
