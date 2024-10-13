"use strict";

function spoilerToggle(e) {
    console.log(e.target, e.currentTarget)
    e.currentTarget.parentElement.classList.toggle("spoiler_open");
    e.stopPropagation();
    // e.preventDefault();
    return e;
}

function indexSpoilerToggle(e) {
    e.currentTarget.parentElement.classList.toggle("index_spoiler_open");
    e.stopPropagation();
    // e.preventDefault();
    return e;
}


window.onload = function() {
  document.querySelectorAll(".spoiler_title").forEach(p => p.addEventListener('click', spoilerToggle, true));
  document.querySelectorAll(".index_spoiler_title").forEach(p => p.addEventListener('click', indexSpoilerToggle, true));
};