function openNav() {
  document.querySelector(".sidebar").classList.remove("close");
}

function closeNav() {
  document.querySelector(".sidebar").classList.add("close");
}

document.querySelector(".toggle").addEventListener("click", function () {
  var sidebar = document.querySelector(".sidebar");
  sidebar.classList.contains("close") ? openNav() : closeNav();
});