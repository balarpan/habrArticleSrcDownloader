"use strict";

function spoilerToggle(e) {
    e.srcElement.parentElement.classList.toggle("spoiler_open");
}
window.onload = function() {
  document.querySelectorAll(".spoiler_title").forEach(p => addEventListener('click', spoilerToggle));
};