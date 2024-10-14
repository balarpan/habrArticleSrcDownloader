"use strict";

// function firstChildWithClass(elem, cls){
//     for (const child of elem.children) {
//         if (child.classList.contains(cls))
//             return child;
//     }
//     return;
// }

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

function indexAuthorSearch(e) {
    let srch_txt = e.currentTarget.value;

    let alist = e.currentTarget.parentElement.parentElement.querySelector('.author_list');
    if (!alist) {
        e.stopPropagation();
        return;    
    }
    let avalues = alist.querySelectorAll("li .index_spoiler_title ").forEach(al=> {
        al.querySelectorAll('.author').forEach(author=> {
            let ctrl = author.parentElement.parentElement;
            if ( author.innerHTML.startsWith(srch_txt) )
                ctrl.style.display = 'block';
            else
                ctrl.style.display = 'none'
        })
    })
    //avalues.querySelector('.author')

    e.stopPropagation();
}

window.onload = function() {
  document.querySelectorAll(".spoiler_title").forEach(p => p.addEventListener('click', spoilerToggle, true));
  document.querySelectorAll(".index_spoiler_title").forEach(p => p.addEventListener('click', indexSpoilerToggle, true));

  let srch_author = document.getElementById('index_author_srch_cnt');
  if (srch_author) {
    srch_author.insertAdjacentHTML('afterbegin', '<input type="text" placeholder="Найти.." pattern=".*\s+.*"><span class="search-btn">\
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#657789" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="search-btn-svg"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></span>');
    srch_author.classList.add('index_srch_cnt');
    srch_author.firstChild.addEventListener('change', indexAuthorSearch, true);
    srch_author.firstChild.addEventListener('input', indexAuthorSearch, true);
  }
};