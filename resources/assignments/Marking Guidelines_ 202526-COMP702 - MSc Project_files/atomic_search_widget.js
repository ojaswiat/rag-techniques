"use strict";(()=>{var R=`.ajas-search-widget {
  --svg-fill: #01579b;
  --close-fill: #fff;
  max-width: 200px;
  width: 100%;
  position: relative;
}

.ajas-search-widget--dashboard {
  margin-right: 10px;
}

.ajas-search-widget--all-courses {
  position: absolute;
  top: 32px;
  right: 24px;
  margin: 0;
}

.ajas-search-widget,
.ajas-search-widget * {
  box-sizing: border-box;
  -webkit-box-sizing: border-box;
  -moz-box-sizing: border-box;
}

.ajas-search-widget__form {
  display: block;
  position: relative;
  width: 100%;
  margin: 0;
}
.ajas-search-widget__form p {
  display: none;
  position: absolute;
  right: 0;
  bottom: -16px;
  text-align: right;
  font-size: 10px;
  color: #777;
  margin-block: 4px 0;
}
.ajas-search-widget__form p span {
  color: var(--svg-fill);
}
.ajas-search-widget__form input {
  height: 36px;
  font-family: "Lato Extended", "Lato", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px;
  color: #202122;
  width: 100%;
  padding-inline: 12px 42px;
  border: 1px solid #8d959f;
  border-radius: 4px;
  background-color: white;
}
.ajas-search-widget__form input:focus {
  border-color: #006fbf;
  outline: 1px solid #006fbf;
}

.ajas-search-widget-hidden {
  position: absolute;
  left: -10000px;
  top: auto;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

.ajas-search-widget__dropdown {
  position: absolute;
  right: 0;
  top: 32px;
  border: 1px solid var(---e5e7eb);
  box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.1607843137);
  border: 1px solid #e5e7eb;
  border-radius: 3px;
  color: #384151;
  z-index: 191;
}

.ajas-search-widget__overlay {
  position: fixed;
  top: 0;
  right: 0;
  width: 100vw;
  height: 100vh;
  z-index: 100;
}

.ajas-search-widget__dropdown.hidden,
.ajas-search-widget__overlay.hidden {
  display: none;
}

.ajas-search-widget__dropdown button {
  padding: 9px 12px;
  letter-spacing: 0px;
  font-size: 14px;
  white-space: nowrap;
  border: none;
  background-color: white;
  color: #202122;
}

.ajas-search-widget__dropdown button:hover {
  cursor: pointer;
  background-color: #eee;
}

@media (max-width: 767px) {
  .ajas-search-widget {
    display: none;
  }
  .ajas-search-widget.ajas-search-widget--small {
    display: block;
  }
}
.ajas-search-toggle {
  width: 45px;
  height: 55px;
  background: none;
  border-radius: 3px;
  border: 1px solid transparent;
  display: grid;
  place-items: center;
  transition: all 0.1s ease;
}
.ajas-search-toggle .ajas-search-logo {
  height: 24px;
  width: 24px;
}
.ajas-search-toggle .ajas-search-logo .logo-path {
  transition: all 100ms ease;
  fill: var(--close-fill);
}
.ajas-search-toggle .ajas-search-logo .logo-rect {
  fill: none;
}
.ajas-search-toggle .ajas-close-svg {
  height: 24px;
  width: 24px;
  fill: var(--close-fill);
  transition: all 100ms ease;
}
.ajas-search-toggle:focus {
  outline: 2px solid #fff;
  outline-offset: -3px;
}

.ajas-search-widget--small {
  position: initial;
  width: auto;
  transition: all 0.3s ease;
  margin: 0;
}
.ajas-search-widget--small .ajas-close-svg {
  display: none;
}
.ajas-search-widget--small .ajas-search-widget__btn-group {
  right: 14px;
  top: 14px;
}
.ajas-search-widget--small .ajas-search-widget__btn--search {
  width: 34px;
  height: 34px;
}
.ajas-search-widget--small .ajas-search-widget__btn--search svg {
  height: 28px;
  width: 28px;
}
.ajas-search-widget--small .ajas-search-widget__overlay {
  top: -55px;
  left: 0;
}
.ajas-search-widget--small .ajas-search-widget__btn--caret {
  height: 34px;
}
.ajas-search-widget--small .ajas-search-widget__dropdown {
  top: 43px;
}
.ajas-search-widget--small form {
  padding: 10px;
  width: 100%;
  min-height: 65px;
  background-color: white;
  box-shadow: 0 5px 5px rgba(0, 0, 0, 0.2);
  position: absolute;
  left: 0;
  top: 55px;
  appearance: none;
  opacity: 0;
  transform-origin: center top;
  transform: rotateX(90deg);
  transition: transform 0.2s ease, opacity 0.2s ease, appearance 0s linear 0.2s;
  z-index: 99;
}
.ajas-search-widget--small form p {
  position: initial;
}
.ajas-search-widget--small input {
  height: 42px;
  font-size: 16px;
  width: 100%;
  margin: 0;
  line-height: normal;
  color: #222 !important;
}
.ajas-search-widget--small.is-active .ajas-search-toggle .ajas-search-logo {
  display: none;
}
.ajas-search-widget--small.is-active .ajas-search-toggle .ajas-close-svg {
  display: block;
}
.ajas-search-widget--small.is-active form {
  appearance: initial;
  transform: rotateX(0);
  transition: transform 0.2s ease, opacity 0.2s ease, appearance 0s linear 0s;
  opacity: 1;
}

.ajas-search-widget--equella input {
  padding-right: 60px;
}
.ajas-search-widget--equella.ajas-search-widget--small input {
  padding-right: 66px;
}

.ajas-search-widget__btn-group {
  display: flex;
  position: absolute;
  align-items: center;
  right: 4px;
  top: 4px;
  border-radius: 3px;
}

.ajas-search-widget__btn--search {
  display: grid;
  place-items: center;
  height: 28px;
  width: 28px;
  border-radius: 3px;
  background: none;
  border: none;
  padding: 0;
  transition: all 100ms ease;
}
.ajas-search-widget__btn--search .ajas-search-logo {
  height: 24px;
  width: 24px;
}
.ajas-search-widget__btn--search .ajas-search-logo .logo-path {
  transition: all 100ms ease;
  fill: var(--svg-fill);
}
.ajas-search-widget__btn--search .ajas-search-logo .logo-rect {
  fill: none;
}
.ajas-search-widget__btn--search:hover {
  --svg-fill: #fff;
  cursor: pointer;
  background-color: #006fbf;
}
.ajas-search-widget__btn--search:focus {
  outline: none;
}
.ajas-search-widget__btn--search:focus-visible {
  --svg-fill: #fff;
  outline: 2px solid #006fbf;
  outline-offset: 2px;
  background-color: #006fbf;
}

.ajas-search-widget__btn--caret {
  width: 24px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}
.ajas-search-widget__btn--caret svg {
  fill: var(--svg-fill);
}
.ajas-search-widget__btn--caret:hover {
  --svg-fill: #fff;
  cursor: pointer;
  background-color: #006fbf;
}
.ajas-search-widget__btn--caret:focus {
  outline: none;
}
.ajas-search-widget__btn--caret:focus-visible {
  --svg-fill: #fff;
  outline: 2px solid #006fbf;
  outline-offset: 2px;
  background-color: #006fbf;
}`;function p(e){let t=document.createElement("template");return t.innerHTML=e.trim(),t.content.firstChild}var m=`<svg class="ajas-search-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64.8 64.6">
  <g>
    <path class="logo-path" d="M52.5,55.9a5.9,5.9,0,0,1-2.3.4H14.6a8,8,0,0,1-8-8v-32a8,8,0,0,1,8-8H50.2a8,8,0,0,1,8,8v32A8.2,8.2,0,0,1,56.7,53L43.5,39.8a13.6,13.6,0,0,0,2.3-7.5A13.4,13.4,0,1,0,32.4,45.7a12.9,12.9,0,0,0,7.5-2.4Zm-20.1-32a8.4,8.4,0,1,0,8.4,8.4A8.5,8.5,0,0,0,32.4,23.9Z"/>
    <rect class="logo-rect" width="64.7" height="64.7"/>
  </g>
</svg>`,q=`<svg class="ajas-close-svg" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
    <path d="M38 12.83L35.17 10 24 21.17 12.83 10 10 12.83 21.17 24 10 35.17 12.83 38 24 26.83 35.17 38 38 35.17 26.83 24z"/>
    <path d="M0 0h48v48H0z" fill="none"/>
  </svg>`;var h=window.atomicSearchConfig||{accountId:null,externalToolId:null,hasEquella:!1};var C="ATOMIC_SEARCH",I="DEFAULT",b="EQUELLA",D=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" id="body_1" width="9" height="4">
    <g transform="matrix(0.28571433 0 0 0.28571433 0.35714287 -0)">
      <path d="M0.15 0L14.5 14.35L28.85 0L0.15 0" stroke="none" fill="currentFill" fill-rule="nonzero" />
    </g>
  </svg>`;function x(e,t){let a=e.attachShadow({mode:"open"}),s=document.createElement("style");s.textContent=R,a.append(s,p(t)),a.querySelector("form").addEventListener("submit",n=>{let c=a.querySelector("input").value,d=n.submitter.value||I;e.dispatchEvent(new CustomEvent(C,{detail:{searchText:c,searchType:d}}))});let r=a.getElementById("menu-target"),o=a.getElementById("menu-overlay"),i=a.getElementById("menu-dropdown");r&&o&&i&&(r.addEventListener("click",()=>{o.classList.remove("hidden"),i.classList.remove("hidden")}),[o,i].forEach(n=>{n.addEventListener("click",()=>{o.classList.add("hidden"),i.classList.add("hidden")})})),a.querySelector("input").addEventListener("keydown",n=>{n.stopPropagation()})}var g=class extends HTMLElement{constructor(){super(...arguments);this._alreadyConnected=!1}connectedCallback(){this._alreadyConnected||(this._onConnect(),this._alreadyConnected=!0)}updateSearchText(a){let s=a||"";this.shadowRoot.querySelector("input").value=s}};function j(e,t){customElements.get(e)||customElements.define(e,t)}function B(){return h.hasEquella}var _=()=>{let e=B();return{dropdownHtml:e?`
    <button id="menu-target" type="button" aria-label="open dropdown" class="ajas-search-widget__btn--caret">
      ${D}
    </button>
    <div id="menu-overlay" class="ajas-search-widget__overlay hidden"></div>
    <div id="menu-dropdown" class="ajas-search-widget__dropdown hidden">
      <button type="submit" value="${b}">Search openEQUELLA content</button>
    </div>
  `:"",equellaClass:e?"ajas-search-widget--equella":""}};function U(e,t){let{dropdownHtml:a,equellaClass:s}=_();return`<div class="ajas-search-widget ${e} ${s}">
      <form id="ajas-search-form" class="ajas-search-widget__form" action="javascript:void(0);" method="get" role="search">
        <label for="ajas-search01" class="ajas-search-widget-hidden">Search</label>
        <input type="text" placeholder="${t}" id="ajas-search01" aria-describedby="powered-by" />
        <p id="powered-by">Powered by <span>Atomic Search</span></p>
        <div class="ajas-search-widget__btn-group">
          <button type="submit" aria-label="submit search" class="ajas-search-widget__btn--search">
            ${m}
          </button>
          ${a}
        </div>
      </form>
    </div>`}var y=class extends g{_onConnect(){let{cssClass:t,placeholder:a}=this.dataset,s=U(t,a);x(this,s)}};j("atomic-search-desktop-widget",y);function z(e){let{dropdownHtml:t,equellaClass:a}=_();return`<div class="ajas-search-widget ajas-search-widget--small ${a}">
    <button class="ajas-search-toggle" type="button" aria-label="toggle search">
      ${m}
      ${q}
    </button>
    <form class="ajas-search-widget__form" action="javascript:void(0);" method="get" role="search">
      <label for="ajas-search02" class="ajas-search-widget-hidden">Search</label>
      <input type="text" placeholder="${e}" id="ajas-search02" aria-describedby="powered-by" />
      <p id="powered-by">Powered by <span>Atomic Search</span></p>
      <div class="ajas-search-widget__btn-group">
        <button type="submit" aria-label="submit search" class="ajas-search-widget__btn--search">
          ${m}
        </button>
        ${t}
      </div>
    </form>
  </div>`}var v=class extends g{_onConnect(){let{placeholder:t}=this.dataset,a=z(t);x(this,a);let s=this.shadowRoot.querySelector(".ajas-search-toggle"),r=this.shadowRoot.querySelector(".ajas-search-widget--small");s.addEventListener("click",()=>{r.classList.toggle("is-active")})}};j("atomic-search-mobile-widget",v);function L(e){let a=Array.from(document.querySelectorAll("iframe")).find(s=>s.contentWindow===e.source);if(a){let s=a.closest("[role=dialog]");s.parentElement.style.width="888px",s.parentElement.style.maxWidth="100%"}}function f(){let e=window.location.search.substring(1);return new URLSearchParams(e)}var M={ajsearch:"search",ajpage:"page",ajcontext:"context",ajfilters:"filters",ajsmart:"semantic"};function H(e){let t=f(),a={subject:"atomicjolt.searchParams"};for(let[s,r]of Object.entries(M)){let o=t.get(s);o&&(a[r]=o)}e.postMessage(JSON.stringify(a),"*")}function P(e){let t=f();for(let[s,r]of Object.entries(M)){let o=e[r];o?t.set(s,o):t.delete(s)}let a=`?${t.toString()}`;window.history.pushState(null,"",a)}var u;function O(e){document.querySelectorAll("atomic-search-desktop-widget,atomic-search-mobile-widget").forEach(t=>{t.updateSearchText(e)})}function V(e){try{localStorage.setItem("atomicjoltModuleProgress",JSON.stringify({time:Date.now(),data:e}))}catch(t){console.warn("failed to write to localStorage",t)}}function Q(){try{let e=localStorage.getItem("atomicjoltModuleProgress");if(e){let t=JSON.parse(e);if(Date.now()-t.time<36e5)return t.data}return{}}catch(e){return console.warn("failed to read from localStorage",e),{}}}function G(e,t){let a=Q(),s=[];if(e.forEach(o=>{a[o]||s.push(o)}),s.length===0){t(a);return}let r=e.map(o=>new Promise(i=>{fetch(`/courses/${o}/modules/progressions.json?user_id=${window.ENV.current_user_id}`).then(n=>{if(!n.ok)throw new Error("Network response was not ok");return n.text()}).then(n=>{let c=JSON.parse(n.replace(/^while\(1\);/,""));i({[o]:c})}).catch(()=>{i({})})}));Promise.all(r).then(o=>{let i=o.reduce((n,c)=>({...n,...c}),{});t(i),V(i)}).catch(o=>console.error(o))}function J(e,t){e.postMessage(JSON.stringify({subject:"atomicjolt.moduleProgress",moduleProgress:t}),"*")}function k(e){H(e),O(f().get("ajsearch"))}function X(e){if(typeof e.data=="string")try{let t=JSON.parse(e.data);switch(t.subject){case"atomicjolt.requestSearchParams":{u||(u=e.source,window.addEventListener("popstate",()=>k(u))),k(u);break}case"atomicjolt.updateSearchParams":{P(t),O(t.search);break}case"atomicjolt.requestModuleProgress":{e.source.postMessage(JSON.stringify({subject:"atomicjolt.ping"}),{}),t.courseIds&&G(t.courseIds,a=>J(e.source,a));break}case"atomicjolt.expandCanvasTray":{L(e);break}default:break}}catch{}}function F(){window.addEventListener("message",X,!1)}var W=/^\/(courses|accounts)\/[0-9~]+/i,K=/\/external_tools\/[0-9]+/i,Z=["Search","S\xF8k","Buscar","Rechercher","\u0422\u044A\u0440\u0441\u0435\u043D\u0435","Cerca","Hledat","S\xF8g","Suche","\u0391\u03BD\u03B1\u03B6\u03AE\u03C4\u03B7\u03C3\u03B7","Ikastaro","Etsi","Cuardaigh","\u0938\u092D\u0940","Keres\xE9s","\u0548\u0580\u0578\u0576\u0565\u056C","Cari","Cerca","Hem\xEE","Doorzoek","Pesquisar","C\u0103uta\u021Bi","\u041F\u043E\u0438\u0441\u043A","S\xF6k","T\xFCm"];function $(e){return Z.some(t=>e.textContent.trim()===t)||e.textContent.trim().startsWith("Search (")}function Y(){if(h.accountId&&h.externalToolId){let o=`external_tools/${h.externalToolId}`,i=window.location.pathname.match(W);return i?`${i[0]}/${o}`:`/accounts/${h.accountId}/${o}?launch_type=global_navigation`}let e='a[href*="/external_tools/"]',a=Array.from(document.querySelectorAll(`#section-tabs ${e}`)).find(o=>$(o));if(a)return a.href;let r=Array.from(document.querySelectorAll(`#menu ${e}`)).find(o=>{let i=o.querySelector(".menu-item__text");return i&&$(i)});if(r){let o=r.href.match(K),i=window.location.pathname.match(W);return i&&o?`${i[0]}${o[0]}`:r.href}return null}var N="ajas-search-widget";function ee(e){function t(r){let o=`
      <atomic-search-desktop-widget
        id="${N}"
        data-css-class="${r}"
        data-placeholder="${e}"
      ></atomic-search-widget>
    `;return p(o)}let a=window.location.pathname,s=null;if(a==="/"){let r=document.querySelector(".ic-Dashboard-header__actions #DashboardOptionsMenu_Container");r&&(s=t("ajas-search-widget--dashboard"),r.before(s))}else if(a.match(/^\/courses\/?$/i)){let r=document.querySelector(".header-bar");r&&(s=t("ajas-search-widget--all-courses"),r.after(s))}else if(a.match(/^\/courses\/[\d]+\/files\/?$/i)){let r=document.querySelector(".ic-app-crumbs");r&&(s=t("ajas-search-widget--files"),r.after(s))}else{let r=document.querySelector(".right-of-crumbs");r&&(s=t("ajas-search-widget--files"),r.appendChild(s))}return{id:N,widget:s}}var A="ajas-search-widget-mobile";function te(e){let t=document.querySelector(".mobile-header-title");if(t){let a=p(`
      <atomic-search-mobile-widget
        id="${A}"
        data-placeholder="${e}"
      ></atomic-search-widget>
    `);return t.after(a),a.parentElement.style.position="relative",{id:A,widget:a}}return{id:A,widget:null}}var T={ACCOUNTS:"Search this account",COURSES:"Search this course",DASHBOARD:"Search my courses"};function E(e,t){try{if(t>=5||!(window.location.pathname.match(/^\/(accounts|courses)/i)||window.location.pathname==="/"))return;let s=Y();if(!s)return;let r=T.DASHBOARD;window.location.pathname.match(/^\/(accounts)/i)&&(r=T.ACCOUNTS),window.location.pathname.match(/^\/(courses)/i)&&(r=T.COURSES);let{widget:o,id:i}=e(r);if(!o){setTimeout(()=>E(e,t),50);return}o.addEventListener(C,c=>{let{searchText:d,searchType:w}=c.detail;if(u){let l=f();l.set("ajsearch",d),l.set("ajpage","1"),w===b&&l.set("ajcontext","OPEN_EQUELLA"),window.history.pushState(null,"",`?${l.toString()}`),k(u)}else{let l=new URLSearchParams({ajsearch:d,ajpage:"1"});window.location.pathname.match(/\/(discussion_topics)/i)&&l.set("ajfilters","discussion_replies"),w===b&&l.set("ajcontext","OPEN_EQUELLA");let S=s.match(/\?/)?"&":"?";window.location.href=`${s}${S}${l.toString()}`}});let n=new MutationObserver(c=>{let d=!1;c.forEach(w=>{Array.from(w.removedNodes).find(S=>S.id===i)&&(d=!0)}),d&&(n.disconnect(),E(e,t+1))});n.observe(o.parentElement,{childList:!0})}catch(a){console.error("Error adding search widget:",a)}}window.ATOMIC_SEARCH_LOCKED||(window.ATOMIC_SEARCH_LOCKED=!0,F(),E(ee,0),E(te,0));})();
