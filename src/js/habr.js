"use strict";

function spoilerToggle(e) {
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

function indexSearchBox(e, disply_type, filter_txt_selector) {
    let srch_txt = e.currentTarget.value;

    // let alist = e.currentTarget.parentElement.parentElement.querySelector('ul.author_list');
    //go up from our searchbox div and one level up more then get first UL
    let alist = e.currentTarget.parentElement.parentElement.querySelector('ul');

    if (!alist) {
        e.stopPropagation();
        return;    
    }
    function s_cmp(s,t) {
        if (s.startsWith('*'))
            return t.toLowerCase().includes(s.substring(1).toLowerCase())
        else
            return t.toLowerCase().startsWith(s.toLowerCase())
    }
    alist.querySelectorAll(filter_txt_selector).forEach(fvalue=> {
            let ctrl = fvalue.closest("li");
            if ( s_cmp(srch_txt, fvalue.innerHTML) )
                ctrl.style.display = disply_type;
            else
                ctrl.style.display = 'none'
    })
    //avalues.querySelector('.author')

    e.stopPropagation();
}

window.addEventListener('load', function () {
    document.querySelectorAll(".spoiler_title").forEach(p => p.addEventListener('click', spoilerToggle, true));
    document.querySelectorAll(".index_spoiler_title").forEach(p => p.addEventListener('click', indexSpoilerToggle, true));

    let sbox_html = '<input type="text" placeholder="Найти.." pattern="\s+"><span class="search-btn">\
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#657789" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="search-btn-svg"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></span>'
    document.querySelectorAll(".index_author_srch_cnt").forEach(sbox => {
      sbox.insertAdjacentHTML('afterbegin', sbox_html);
      sbox.classList.add('index_srch_cnt');
      sbox.firstChild.addEventListener('change', function(e){indexSearchBox(e,'flex','li .author')}, true);
      sbox.firstChild.addEventListener('input',  function(e){indexSearchBox(e,'flex','li .author')}, true);
    })
    document.querySelectorAll(".index_article_srch_cnt").forEach(sbox => {
      sbox.insertAdjacentHTML('afterbegin', sbox_html);
      sbox.classList.add('index_srch_cnt');
      sbox.firstChild.addEventListener('change', function(e){indexSearchBox(e,'flex','li a.article_link')}, true);
      sbox.firstChild.addEventListener('input',  function(e){indexSearchBox(e,'flex','li a.article_link')}, true);
    })
});
