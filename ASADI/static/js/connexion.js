



//gestion de la visibilité du mot de passe
function togglePassword(idInput, idOpen, idClosed) {
  const input = document.getElementById(idInput);
  const eyeOpen = document.getElementById(idOpen);
  const eyeClosed = document.getElementById(idClosed);

  const isHidden = input.type === "password";
  input.type = isHidden ? "text" : "password";
  eyeOpen.style.display = isHidden ? "none" : "inline";
  eyeClosed.style.display = isHidden ? "inline" : "none";
}