(()=>{var e=document.querySelector("#table-search-services"),c=document.querySelector("#table-search-service-button");c&&e&&c.addEventListener("click",(function(){var c=new URL(window.location.href);c.searchParams.set("q",e.value),window.location.href="".concat(c.href)}))})();