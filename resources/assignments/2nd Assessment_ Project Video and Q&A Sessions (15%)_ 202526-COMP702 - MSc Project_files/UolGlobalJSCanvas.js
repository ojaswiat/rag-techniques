/* ###Blackboard ALLY### */

window.ALLY_CFG = {
    'baseUrl': 'https://prod-eu-central-1.ally.ac',
    'clientId': 403
};
$.getScript(ALLY_CFG.baseUrl + '/integration/canvas/ally.js');

/* ###Atomic Search### */

var atomicSearchWidgetScript = document.createElement("script");
atomicSearchWidgetScript.src = "https://js.atomicsearchwidget.com/atomic_search_widget.js";
document.getElementsByTagName("head")[0].appendChild(atomicSearchWidgetScript);

/* ###H5P### */

var h5pLtiResizerScript=document.createElement('script');
h5pLtiResizerScript.setAttribute('charset','UTF-8');
h5pLtiResizerScript.setAttribute('src','https://h5p.com/canvas-resizer.js');
document.body.appendChild(h5pLtiResizerScript);
 
var h5pEmbedResizerScript=document.createElement('script');
h5pEmbedResizerScript.setAttribute('charset','UTF-8');
h5pEmbedResizerScript.setAttribute('src','https://h5p.com/js/h5p-resizer.js');
document.body.appendChild(h5pEmbedResizerScript);
