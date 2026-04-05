var Ve=Object.defineProperty;var et=Object.getOwnPropertyDescriptor;var l=(i,o,e,t)=>{for(var r=t>1?void 0:t?et(o,e):o,s=i.length-1,n;s>=0;s--)(n=i[s])&&(r=(t?n(o,e,r):n(r))||r);return t&&r&&Ve(o,e,r),r};var Q=globalThis,V=Q.ShadowRoot&&(Q.ShadyCSS===void 0||Q.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,ie=Symbol(),xe=new WeakMap,B=class{constructor(o,e,t){if(this._$cssResult$=!0,t!==ie)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=o,this.t=e}get styleSheet(){let o=this.o,e=this.t;if(V&&o===void 0){let t=e!==void 0&&e.length===1;t&&(o=xe.get(e)),o===void 0&&((this.o=o=new CSSStyleSheet).replaceSync(this.cssText),t&&xe.set(e,o))}return o}toString(){return this.cssText}},_e=i=>new B(typeof i=="string"?i:i+"",void 0,ie),x=(i,...o)=>{let e=i.length===1?i[0]:o.reduce((t,r,s)=>t+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+i[s+1],i[0]);return new B(e,i,ie)},ye=(i,o)=>{if(V)i.adoptedStyleSheets=o.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of o){let t=document.createElement("style"),r=Q.litNonce;r!==void 0&&t.setAttribute("nonce",r),t.textContent=e.cssText,i.appendChild(t)}},ne=V?i=>i:i=>i instanceof CSSStyleSheet?(o=>{let e="";for(let t of o.cssRules)e+=t.cssText;return _e(e)})(i):i;var{is:tt,defineProperty:ot,getOwnPropertyDescriptor:rt,getOwnPropertyNames:st,getOwnPropertySymbols:it,getPrototypeOf:nt}=Object,ee=globalThis,$e=ee.trustedTypes,at=$e?$e.emptyScript:"",lt=ee.reactiveElementPolyfillSupport,G=(i,o)=>i,F={toAttribute(i,o){switch(o){case Boolean:i=i?at:null;break;case Object:case Array:i=i==null?i:JSON.stringify(i)}return i},fromAttribute(i,o){let e=i;switch(o){case Boolean:e=i!==null;break;case Number:e=i===null?null:Number(i);break;case Object:case Array:try{e=JSON.parse(i)}catch{e=null}}return e}},te=(i,o)=>!tt(i,o),we={attribute:!0,type:String,converter:F,reflect:!1,useDefault:!1,hasChanged:te};Symbol.metadata??=Symbol("metadata"),ee.litPropertyMetadata??=new WeakMap;var H=class extends HTMLElement{static addInitializer(o){this._$Ei(),(this.l??=[]).push(o)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(o,e=we){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(o)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(o,e),!e.noAccessor){let t=Symbol(),r=this.getPropertyDescriptor(o,t,e);r!==void 0&&ot(this.prototype,o,r)}}static getPropertyDescriptor(o,e,t){let{get:r,set:s}=rt(this.prototype,o)??{get(){return this[e]},set(n){this[e]=n}};return{get:r,set(n){let c=r?.call(this);s?.call(this,n),this.requestUpdate(o,c,t)},configurable:!0,enumerable:!0}}static getPropertyOptions(o){return this.elementProperties.get(o)??we}static _$Ei(){if(this.hasOwnProperty(G("elementProperties")))return;let o=nt(this);o.finalize(),o.l!==void 0&&(this.l=[...o.l]),this.elementProperties=new Map(o.elementProperties)}static finalize(){if(this.hasOwnProperty(G("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(G("properties"))){let e=this.properties,t=[...st(e),...it(e)];for(let r of t)this.createProperty(r,e[r])}let o=this[Symbol.metadata];if(o!==null){let e=litPropertyMetadata.get(o);if(e!==void 0)for(let[t,r]of e)this.elementProperties.set(t,r)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let r=this._$Eu(e,t);r!==void 0&&this._$Eh.set(r,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(o){let e=[];if(Array.isArray(o)){let t=new Set(o.flat(1/0).reverse());for(let r of t)e.unshift(ne(r))}else o!==void 0&&e.push(ne(o));return e}static _$Eu(o,e){let t=e.attribute;return t===!1?void 0:typeof t=="string"?t:typeof o=="string"?o.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(o=>this.enableUpdating=o),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(o=>o(this))}addController(o){(this._$EO??=new Set).add(o),this.renderRoot!==void 0&&this.isConnected&&o.hostConnected?.()}removeController(o){this._$EO?.delete(o)}_$E_(){let o=new Map,e=this.constructor.elementProperties;for(let t of e.keys())this.hasOwnProperty(t)&&(o.set(t,this[t]),delete this[t]);o.size>0&&(this._$Ep=o)}createRenderRoot(){let o=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ye(o,this.constructor.elementStyles),o}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(o=>o.hostConnected?.())}enableUpdating(o){}disconnectedCallback(){this._$EO?.forEach(o=>o.hostDisconnected?.())}attributeChangedCallback(o,e,t){this._$AK(o,t)}_$ET(o,e){let t=this.constructor.elementProperties.get(o),r=this.constructor._$Eu(o,t);if(r!==void 0&&t.reflect===!0){let s=(t.converter?.toAttribute!==void 0?t.converter:F).toAttribute(e,t.type);this._$Em=o,s==null?this.removeAttribute(r):this.setAttribute(r,s),this._$Em=null}}_$AK(o,e){let t=this.constructor,r=t._$Eh.get(o);if(r!==void 0&&this._$Em!==r){let s=t.getPropertyOptions(r),n=typeof s.converter=="function"?{fromAttribute:s.converter}:s.converter?.fromAttribute!==void 0?s.converter:F;this._$Em=r;let c=n.fromAttribute(e,s.type);this[r]=c??this._$Ej?.get(r)??c,this._$Em=null}}requestUpdate(o,e,t,r=!1,s){if(o!==void 0){let n=this.constructor;if(r===!1&&(s=this[o]),t??=n.getPropertyOptions(o),!((t.hasChanged??te)(s,e)||t.useDefault&&t.reflect&&s===this._$Ej?.get(o)&&!this.hasAttribute(n._$Eu(o,t))))return;this.C(o,e,t)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(o,e,{useDefault:t,reflect:r,wrapped:s},n){t&&!(this._$Ej??=new Map).has(o)&&(this._$Ej.set(o,n??e??this[o]),s!==!0||n!==void 0)||(this._$AL.has(o)||(this.hasUpdated||t||(e=void 0),this._$AL.set(o,e)),r===!0&&this._$Em!==o&&(this._$Eq??=new Set).add(o))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let o=this.scheduleUpdate();return o!=null&&await o,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,s]of this._$Ep)this[r]=s;this._$Ep=void 0}let t=this.constructor.elementProperties;if(t.size>0)for(let[r,s]of t){let{wrapped:n}=s,c=this[r];n!==!0||this._$AL.has(r)||c===void 0||this.C(r,void 0,s,c)}}let o=!1,e=this._$AL;try{o=this.shouldUpdate(e),o?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(t){throw o=!1,this._$EM(),t}o&&this._$AE(e)}willUpdate(o){}_$AE(o){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(o)),this.updated(o)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(o){return!0}update(o){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(o){}firstUpdated(o){}};H.elementStyles=[],H.shadowRootOptions={mode:"open"},H[G("elementProperties")]=new Map,H[G("finalized")]=new Map,lt?.({ReactiveElement:H}),(ee.reactiveElementVersions??=[]).push("2.1.2");var he=globalThis,Ee=i=>i,oe=he.trustedTypes,ke=oe?oe.createPolicy("lit-html",{createHTML:i=>i}):void 0,De="$lit$",T=`lit$${Math.random().toFixed(9).slice(2)}$`,He="?"+T,ct=`<${He}>`,M=document,W=()=>M.createComment(""),q=i=>i===null||typeof i!="object"&&typeof i!="function",ge=Array.isArray,dt=i=>ge(i)||typeof i?.[Symbol.iterator]=="function",ae=`[ 	
\f\r]`,j=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Se=/-->/g,Ae=/>/g,I=RegExp(`>|${ae}(?:([^\\s"'>=/]+)(${ae}*=${ae}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ce=/'/g,Le=/"/g,Te=/^(?:script|style|textarea|title)$/i,me=i=>(o,...e)=>({_$litType$:i,strings:o,values:e}),a=me(1),St=me(2),At=me(3),U=Symbol.for("lit-noChange"),v=Symbol.for("lit-nothing"),Re=new WeakMap,O=M.createTreeWalker(M,129);function ze(i,o){if(!ge(i)||!i.hasOwnProperty("raw"))throw Error("invalid template strings array");return ke!==void 0?ke.createHTML(o):o}var pt=(i,o)=>{let e=i.length-1,t=[],r,s=o===2?"<svg>":o===3?"<math>":"",n=j;for(let c=0;c<e;c++){let d=i[c],u,h,g=-1,$=0;for(;$<d.length&&(n.lastIndex=$,h=n.exec(d),h!==null);)$=n.lastIndex,n===j?h[1]==="!--"?n=Se:h[1]!==void 0?n=Ae:h[2]!==void 0?(Te.test(h[2])&&(r=RegExp("</"+h[2],"g")),n=I):h[3]!==void 0&&(n=I):n===I?h[0]===">"?(n=r??j,g=-1):h[1]===void 0?g=-2:(g=n.lastIndex-h[2].length,u=h[1],n=h[3]===void 0?I:h[3]==='"'?Le:Ce):n===Le||n===Ce?n=I:n===Se||n===Ae?n=j:(n=I,r=void 0);let R=n===I&&i[c+1].startsWith("/>")?" ":"";s+=n===j?d+ct:g>=0?(t.push(u),d.slice(0,g)+De+d.slice(g)+T+R):d+T+(g===-2?c:R)}return[ze(i,s+(i[e]||"<?>")+(o===2?"</svg>":o===3?"</math>":"")),t]},J=class i{constructor({strings:o,_$litType$:e},t){let r;this.parts=[];let s=0,n=0,c=o.length-1,d=this.parts,[u,h]=pt(o,e);if(this.el=i.createElement(u,t),O.currentNode=this.el.content,e===2||e===3){let g=this.el.content.firstChild;g.replaceWith(...g.childNodes)}for(;(r=O.nextNode())!==null&&d.length<c;){if(r.nodeType===1){if(r.hasAttributes())for(let g of r.getAttributeNames())if(g.endsWith(De)){let $=h[n++],R=r.getAttribute(g).split(T),Z=/([.?@])?(.*)/.exec($);d.push({type:1,index:s,name:Z[2],strings:R,ctor:Z[1]==="."?ce:Z[1]==="?"?de:Z[1]==="@"?pe:N}),r.removeAttribute(g)}else g.startsWith(T)&&(d.push({type:6,index:s}),r.removeAttribute(g));if(Te.test(r.tagName)){let g=r.textContent.split(T),$=g.length-1;if($>0){r.textContent=oe?oe.emptyScript:"";for(let R=0;R<$;R++)r.append(g[R],W()),O.nextNode(),d.push({type:2,index:++s});r.append(g[$],W())}}}else if(r.nodeType===8)if(r.data===He)d.push({type:2,index:s});else{let g=-1;for(;(g=r.data.indexOf(T,g+1))!==-1;)d.push({type:7,index:s}),g+=T.length-1}s++}}static createElement(o,e){let t=M.createElement("template");return t.innerHTML=o,t}};function P(i,o,e=i,t){if(o===U)return o;let r=t!==void 0?e._$Co?.[t]:e._$Cl,s=q(o)?void 0:o._$litDirective$;return r?.constructor!==s&&(r?._$AO?.(!1),s===void 0?r=void 0:(r=new s(i),r._$AT(i,e,t)),t!==void 0?(e._$Co??=[])[t]=r:e._$Cl=r),r!==void 0&&(o=P(i,r._$AS(i,o.values),r,t)),o}var le=class{constructor(o,e){this._$AV=[],this._$AN=void 0,this._$AD=o,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(o){let{el:{content:e},parts:t}=this._$AD,r=(o?.creationScope??M).importNode(e,!0);O.currentNode=r;let s=O.nextNode(),n=0,c=0,d=t[0];for(;d!==void 0;){if(n===d.index){let u;d.type===2?u=new Y(s,s.nextSibling,this,o):d.type===1?u=new d.ctor(s,d.name,d.strings,this,o):d.type===6&&(u=new ue(s,this,o)),this._$AV.push(u),d=t[++c]}n!==d?.index&&(s=O.nextNode(),n++)}return O.currentNode=M,r}p(o){let e=0;for(let t of this._$AV)t!==void 0&&(t.strings!==void 0?(t._$AI(o,t,e),e+=t.strings.length-2):t._$AI(o[e])),e++}},Y=class i{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(o,e,t,r){this.type=2,this._$AH=v,this._$AN=void 0,this._$AA=o,this._$AB=e,this._$AM=t,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let o=this._$AA.parentNode,e=this._$AM;return e!==void 0&&o?.nodeType===11&&(o=e.parentNode),o}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(o,e=this){o=P(this,o,e),q(o)?o===v||o==null||o===""?(this._$AH!==v&&this._$AR(),this._$AH=v):o!==this._$AH&&o!==U&&this._(o):o._$litType$!==void 0?this.$(o):o.nodeType!==void 0?this.T(o):dt(o)?this.k(o):this._(o)}O(o){return this._$AA.parentNode.insertBefore(o,this._$AB)}T(o){this._$AH!==o&&(this._$AR(),this._$AH=this.O(o))}_(o){this._$AH!==v&&q(this._$AH)?this._$AA.nextSibling.data=o:this.T(M.createTextNode(o)),this._$AH=o}$(o){let{values:e,_$litType$:t}=o,r=typeof t=="number"?this._$AC(o):(t.el===void 0&&(t.el=J.createElement(ze(t.h,t.h[0]),this.options)),t);if(this._$AH?._$AD===r)this._$AH.p(e);else{let s=new le(r,this),n=s.u(this.options);s.p(e),this.T(n),this._$AH=s}}_$AC(o){let e=Re.get(o.strings);return e===void 0&&Re.set(o.strings,e=new J(o)),e}k(o){ge(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,t,r=0;for(let s of o)r===e.length?e.push(t=new i(this.O(W()),this.O(W()),this,this.options)):t=e[r],t._$AI(s),r++;r<e.length&&(this._$AR(t&&t._$AB.nextSibling,r),e.length=r)}_$AR(o=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);o!==this._$AB;){let t=Ee(o).nextSibling;Ee(o).remove(),o=t}}setConnected(o){this._$AM===void 0&&(this._$Cv=o,this._$AP?.(o))}},N=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(o,e,t,r,s){this.type=1,this._$AH=v,this._$AN=void 0,this.element=o,this.name=e,this._$AM=r,this.options=s,t.length>2||t[0]!==""||t[1]!==""?(this._$AH=Array(t.length-1).fill(new String),this.strings=t):this._$AH=v}_$AI(o,e=this,t,r){let s=this.strings,n=!1;if(s===void 0)o=P(this,o,e,0),n=!q(o)||o!==this._$AH&&o!==U,n&&(this._$AH=o);else{let c=o,d,u;for(o=s[0],d=0;d<s.length-1;d++)u=P(this,c[t+d],e,d),u===U&&(u=this._$AH[d]),n||=!q(u)||u!==this._$AH[d],u===v?o=v:o!==v&&(o+=(u??"")+s[d+1]),this._$AH[d]=u}n&&!r&&this.j(o)}j(o){o===v?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,o??"")}},ce=class extends N{constructor(){super(...arguments),this.type=3}j(o){this.element[this.name]=o===v?void 0:o}},de=class extends N{constructor(){super(...arguments),this.type=4}j(o){this.element.toggleAttribute(this.name,!!o&&o!==v)}},pe=class extends N{constructor(o,e,t,r,s){super(o,e,t,r,s),this.type=5}_$AI(o,e=this){if((o=P(this,o,e,0)??v)===U)return;let t=this._$AH,r=o===v&&t!==v||o.capture!==t.capture||o.once!==t.once||o.passive!==t.passive,s=o!==v&&(t===v||r);r&&this.element.removeEventListener(this.name,this,t),s&&this.element.addEventListener(this.name,this,o),this._$AH=o}handleEvent(o){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,o):this._$AH.handleEvent(o)}},ue=class{constructor(o,e,t){this.element=o,this.type=6,this._$AN=void 0,this._$AM=e,this.options=t}get _$AU(){return this._$AM._$AU}_$AI(o){P(this,o)}};var ut=he.litHtmlPolyfillSupport;ut?.(J,Y),(he.litHtmlVersions??=[]).push("3.3.2");var Ie=(i,o,e)=>{let t=e?.renderBefore??o,r=t._$litPart$;if(r===void 0){let s=e?.renderBefore??null;t._$litPart$=r=new Y(o.insertBefore(W(),s),s,void 0,e??{})}return r._$AI(i),r};var ve=globalThis,f=class extends H{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let o=super.createRenderRoot();return this.renderOptions.renderBefore??=o.firstChild,o}update(o){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(o),this._$Do=Ie(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return U}};f._$litElement$=!0,f.finalized=!0,ve.litElementHydrateSupport?.({LitElement:f});var ht=ve.litElementPolyfillSupport;ht?.({LitElement:f});(ve.litElementVersions??=[]).push("4.2.2");var y=i=>(o,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(i,o)}):customElements.define(i,o)};var gt={attribute:!0,type:String,converter:F,reflect:!1,hasChanged:te},mt=(i=gt,o,e)=>{let{kind:t,metadata:r}=e,s=globalThis.litPropertyMetadata.get(r);if(s===void 0&&globalThis.litPropertyMetadata.set(r,s=new Map),t==="setter"&&((i=Object.create(i)).wrapped=!0),s.set(e.name,i),t==="accessor"){let{name:n}=e;return{set(c){let d=o.get.call(this);o.set.call(this,c),this.requestUpdate(n,d,i,!0,c)},init(c){return c!==void 0&&this.C(n,void 0,i,c),c}}}if(t==="setter"){let{name:n}=e;return function(c){let d=this[n];o.call(this,c),this.requestUpdate(n,d,i,!0,c)}}throw Error("Unsupported decorator location: "+t)};function m(i){return(o,e)=>typeof e=="object"?mt(i,o,e):((t,r,s)=>{let n=r.hasOwnProperty(s);return r.constructor.createProperty(s,t),n?Object.getOwnPropertyDescriptor(r,s):void 0})(i,o,e)}function p(i){return m({...i,state:!0,attribute:!1})}async function Oe(i){return i.callWS({type:"loxone/list_entries"})}async function K(i,o){return i.callWS({type:"loxone/get_devices",...o?{miniserver:o}:{}})}async function Me(i,o,e){return i.callWS({type:"loxone/set_entity_enabled",entity_id:o,enabled:e})}async function Ue(i,o){return i.callWS({type:"loxone/get_areas",...o?{miniserver:o}:{}})}async function Pe(i,o){await i.callService("loxone","sync_areas",{create_areas:o})}async function Ne(i){await i.callService("loxone","sync_device_names")}async function Ke(i,o){return i.callWS({type:"loxone/get_bridges",...o?{miniserver:o}:{}})}async function Be(i,o,e,t,r){return i.callWS({type:"loxone/add_bridge",entity_id:o,loxone_uuid:e,...t?{miniserver:t}:{},...r&&Object.keys(r).length>0?{details:r}:{}})}async function Ge(i,o,e){return i.callWS({type:"loxone/remove_bridge",entity_id:o,...e?{miniserver:e}:{}})}async function Fe(i,o){return i.callWS({type:"loxone/get_status",...o?{miniserver:o}:{}})}async function je(i,o){return i.callWS({type:"loxone/get_structure_diff",...o?{miniserver:o}:{}})}async function We(i,o,e,t){return i.callWS({type:"loxone/send_command",uuid:o,command:e,...t?{miniserver:t}:{}})}async function qe(i,o,e){return i.callWS({type:"loxone/get_control_detail",uuid:o,...e?{miniserver:e}:{}})}async function Je(i,o){return i.callWS({type:"loxone/get_structure",...o?{miniserver:o}:{}})}function S(i,o){i.dispatchEvent(new CustomEvent("hass-notification",{bubbles:!0,composed:!0,detail:{message:o,duration:4e3}}))}var _=class extends f{constructor(){super(...arguments);this.refreshKey=0;this._devices=[];this._filter="";this._filterDomain="";this._filterRoom="";this._filterStatus="";this._loading=!0;this._error="";this._sortKey="room";this._sortDir="asc";this._detail=null;this._detailLoading=!1}connectedCallback(){super.connectedCallback(),this._loadDevices()}updated(e){e.has("refreshKey")&&e.get("refreshKey")!==void 0&&this._loadDevices()}async _loadDevices(){this._loading=!0,this._error="";try{let e=await K(this.hass,this.miniserverId);this._devices=e.devices}catch(e){this._error=e instanceof Error?e.message:String(e)}finally{this._loading=!1}}get _allDomains(){let e=new Set;for(let t of this._devices)for(let r of t.ha_entities)e.add(r.entity_id.split(".")[0]);return[...e].sort()}get _allRooms(){let e=new Set;for(let t of this._devices)t.room&&e.add(t.room);return[...e].sort()}get _filteredDevices(){let e=this._devices;if(this._filter){let t=this._filter.toLowerCase();e=e.filter(r=>r.name.toLowerCase().includes(t)||r.type.toLowerCase().includes(t)||r.room.toLowerCase().includes(t)||r.ha_entities.some(s=>s.entity_id.toLowerCase().includes(t)))}if(this._filterDomain){let t=this._filterDomain;e=e.filter(r=>r.ha_entities.some(s=>s.entity_id.startsWith(t+".")))}if(this._filterRoom&&(e=e.filter(t=>t.room===this._filterRoom)),this._filterStatus)switch(this._filterStatus){case"enabled":e=e.filter(t=>t.ha_entities.length>0&&t.ha_entities.some(r=>!r.disabled_by));break;case"disabled":e=e.filter(t=>t.ha_entities.some(r=>!!r.disabled_by));break;case"no-entity":e=e.filter(t=>t.ha_entities.length===0);break}return this._sortDevices(e)}_sortDevices(e){let t=this._sortDir==="asc"?1:-1,r=(u,h)=>{let g=0;switch(this._sortKey){case"name":g=u.name.localeCompare(h.name);break;case"type":g=u.type.localeCompare(h.type)||u.name.localeCompare(h.name);break;case"room":g=(u.room||"").localeCompare(h.room||"")||u.name.localeCompare(h.name);break;case"entities":g=u.ha_entities.length-h.ha_entities.length;break}return g*t},s=new Set(e.filter(u=>!u.parent).map(u=>u.uuid)),n=new Map,c=[];for(let u of e)if(u.parent&&s.has(u.parent)){let h=n.get(u.parent)||[];h.push(u),n.set(u.parent,h)}else c.push(u);c.sort(r);for(let u of n.values())u.sort(r);let d=[];for(let u of c){d.push(u);let h=n.get(u.uuid);h&&d.push(...h)}return d}_toggleSort(e){this._sortKey===e?this._sortDir=this._sortDir==="asc"?"desc":"asc":(this._sortKey=e,this._sortDir="asc")}_sortIndicator(e){return this._sortKey!==e?v:a`<span class="sort-arrow"
      >${this._sortDir==="asc"?"\u25B2":"\u25BC"}</span
    >`}async _openDetail(e){this._detailLoading=!0,this._detail=null;try{this._detail=await qe(this.hass,e,this.miniserverId)}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._detailLoading=!1}}_closeDetail(){this._detail=null}async _toggleEntity(e,t){try{await Me(this.hass,e,t),S(this,`${e} ${t?"enabled":"disabled"}`),await this._loadDevices()}catch(r){this._error=r instanceof Error?r.message:String(r)}}render(){if(this._loading)return a`<p class="status">Loading devices…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let e=this._filteredDevices,t=new Set(e.map(c=>c.uuid)),r=new Map;for(let c of this._devices)for(let d of c.ha_entities){let u=d.entity_id.split(".")[0];r.set(u,(r.get(u)||0)+1)}let s=[...r.values()].reduce((c,d)=>c+d,0),n=[...r.entries()].sort((c,d)=>d[1]-c[1]).map(([c,d])=>`${d} ${c}`).join(", ");return a`
      <p class="page-intro">
        All Loxone controls discovered from the structure file, alongside their Home Assistant entities.
        Click any row to inspect live state, UUIDs, and sub-controls.
        Use the ✓ toggle on an entity chip to enable or disable it without removing it.
      </p>
      <div class="toolbar">
        <input
          type="search"
          placeholder="Filter by name, type, room, or entity…"
          .value=${this._filter}
          @input=${c=>{this._filter=c.target.value}}
        />
        <select class="filter-select" .value=${this._filterDomain}
          @change=${c=>{this._filterDomain=c.target.value}}>
          <option value="">All domains</option>
          ${this._allDomains.map(c=>a`<option value=${c}>${c}</option>`)}
        </select>
        <select class="filter-select" .value=${this._filterRoom}
          @change=${c=>{this._filterRoom=c.target.value}}>
          <option value="">All rooms</option>
          ${this._allRooms.map(c=>a`<option value=${c}>${c}</option>`)}
        </select>
        <select class="filter-select" .value=${this._filterStatus}
          @change=${c=>{this._filterStatus=c.target.value}}>
          <option value="">All statuses</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
          <option value="no-entity">No entity</option>
        </select>
      </div>
      <p class="summary">
        <span class="count">${this._devices.length}</span> controls,
        <span class="count">${s}</span> HA entities
        ${n?a`<span class="domain-breakdown">(${n})</span>`:""}
      </p>
      <table>
        <thead>
          <tr>
            <th
              class=${this._sortKey==="name"?"active":""}
              @click=${()=>this._toggleSort("name")}
            >
              Name${this._sortIndicator("name")}
            </th>
            <th
              class=${this._sortKey==="type"?"active":""}
              @click=${()=>this._toggleSort("type")}
            >
              Type${this._sortIndicator("type")}
            </th>
            <th
              class=${this._sortKey==="room"?"active":""}
              @click=${()=>this._toggleSort("room")}
            >
              Room${this._sortIndicator("room")}
            </th>
            <th
              class=${this._sortKey==="entities"?"active":""}
              @click=${()=>this._toggleSort("entities")}
            >
              HA Entities${this._sortIndicator("entities")}
            </th>
          </tr>
        </thead>
        <tbody>
          ${e.map(c=>a`
              <tr class="${c.parent&&t.has(c.parent)?"sub-control":""} clickable"
                  @click=${()=>this._openDetail(c.uuid)}>
                <td>${c.name}</td>
                <td><span class="badge">${c.type}</span></td>
                <td>${c.room||"\u2014"}</td>
                <td>
                  ${c.ha_entities.length===0?a`<span style="color: var(--secondary-text-color)"
                        >—</span
                      >`:c.ha_entities.map(d=>a`
                          <span
                            class="entity-chip ${d.disabled_by?"disabled":""}"
                          >
                            ${d.entity_id}
                            <button
                              type="button"
                              class="toggle-btn"
                              title=${d.disabled_by?"Enable":"Disable"}
                              aria-label=${d.disabled_by?`Enable ${d.entity_id}`:`Disable ${d.entity_id}`}
                              @click=${u=>{u.stopPropagation(),this._toggleEntity(d.entity_id,!!d.disabled_by)}}
                            >
                              ${d.disabled_by?"\u2B1A":"\u2713"}
                            </button>
                          </span>
                        `)}
                </td>
              </tr>
            `)}
        </tbody>
      </table>
      ${this._detailLoading?a`<div class="drawer-overlay"><div class="drawer"><p class="status">Loading…</p></div></div>`:""}
      ${this._detail?this._renderDrawer(this._detail):""}
    `}_renderDrawer(e){let t=Object.entries(e.states);return a`
      <div class="drawer-overlay" @click=${this._closeDetail}></div>
      <div class="drawer" @click=${r=>r.stopPropagation()}>
        <button
          type="button"
          class="close-btn"
          aria-label="Close control details"
          @click=${this._closeDetail}
        >
          ✕
        </button>
        <h2>${e.name}</h2>
        <div class="sub-title">
          <span class="badge">${e.type}</span>
          ${e.room?a` — ${e.room}`:""}
          ${e.category?a` — ${e.category}`:""}
          ${e.is_sub_control&&e.parent_name?a` (sub-control of ${e.parent_name})`:""}
        </div>
        <div class="detail-row">
          <span class="detail-label">UUID</span>
          <span class="detail-value">${e.uuid}</span>
        </div>
        ${t.length>0?a`
          <div class="section-title">States (${t.length})</div>
          ${t.map(([r,s])=>a`
            <div class="detail-row">
              <span class="detail-label">${r}</span>
              <span class="detail-value">${s.value??"\u2014"}${s.last_changed?a` <span style="opacity:0.5;font-size:11px">${new Date(s.last_changed).toLocaleTimeString()}</span>`:""}</span>
            </div>
          `)}
        `:""}
        ${e.ha_entities.length>0?a`
          <div class="section-title">HA Entities (${e.ha_entities.length})</div>
          ${e.ha_entities.map(r=>a`
            <div class="entity-row">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span>${r.entity_id}</span>
                <span class="badge" style="${r.disabled_by?"background:var(--disabled-text-color,#bdbdbd)":"background:var(--success-color,#4caf50);color:#fff"}">${r.disabled_by?"disabled":r.state??"\u2014"}</span>
              </div>
              ${r.last_changed?a`<div style="font-size:11px;color:var(--secondary-text-color);margin-top:2px">Last changed: ${new Date(r.last_changed).toLocaleString()}</div>`:""}
            </div>
          `)}
        `:a`<div class="section-title">No HA entities</div>`}
        ${Object.keys(e.details).length>0?a`
          <div class="section-title">Details</div>
          ${Object.entries(e.details).map(([r,s])=>a`
            <div class="detail-row">
              <span class="detail-label">${r}</span>
              <span class="detail-value">${typeof s=="object"?JSON.stringify(s):String(s)}</span>
            </div>
          `)}
        `:""}
      </div>
    `}};_.styles=x`
    :host {
      display: block;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    input[type="search"] {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      flex: 1;
      min-width: 200px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
    }
    .filter-select {
      padding: 8px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer; min-width: 100px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    th {
      text-align: left;
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      background: var(--table-header-background-color, var(--card-background-color, #fff));
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }
    th:hover {
      color: var(--primary-text-color, #212121);
    }
    th.active {
      color: var(--primary-color, #03a9f4);
    }
    .sort-arrow {
      font-size: 10px;
      margin-left: 4px;
    }
    td {
      padding: 10px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      vertical-align: top;
    }
    tr:last-child td {
      border-bottom: none;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    tr.sub-control td:first-child {
      padding-left: 32px;
    }
    .entity-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      margin: 2px 2px;
    }
    .entity-chip.disabled {
      background: var(--disabled-text-color, #bdbdbd);
    }
    .toggle-btn {
      border: none;
      background: none;
      cursor: pointer;
      font-size: 16px;
      padding: 2px 4px;
      border-radius: 4px;
      line-height: 1;
    }
    .toggle-btn:hover {
      background: var(--divider-color, #e0e0e0);
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 500;
      background: var(--divider-color, #e0e0e0);
      color: var(--secondary-text-color, #727272);
    }
    .status {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 16px;
    }
    .error {
      color: var(--error-color, #db4437);
    }
    .count {
      font-weight: 500;
      color: var(--primary-color, #03a9f4);
    }
    .summary {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin-bottom: 8px;
    }
    .domain-breakdown {
      color: var(--secondary-text-color, #727272);
      font-size: 12px;
    }
    tr.clickable { cursor: pointer; }
    tr.clickable:hover td { background: var(--table-row-alternative-background-color, #fafafa); }
    .drawer-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.4); z-index: 100;
    }
    .drawer {
      position: fixed; top: 0; right: 0; bottom: 0; width: min(520px, 90vw);
      background: var(--primary-background-color, #fafafa);
      box-shadow: -4px 0 20px rgba(0,0,0,0.15); z-index: 101;
      overflow-y: auto; padding: 24px; box-sizing: border-box;
    }
    .drawer h2 { font-size: 18px; font-weight: 500; margin: 0 0 4px; }
    .drawer .sub-title { font-size: 13px; color: var(--secondary-text-color); margin-bottom: 16px; }
    .drawer .close-btn {
      position: absolute; top: 16px; right: 16px;
      border: none; background: none; font-size: 20px; cursor: pointer;
      color: var(--secondary-text-color);
    }
    .drawer .section-title {
      font-size: 12px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.5px; color: var(--secondary-text-color);
      margin: 16px 0 8px; border-bottom: 1px solid var(--divider-color, #e0e0e0);
      padding-bottom: 4px;
    }
    .drawer .detail-row {
      display: flex; justify-content: space-between; align-items: baseline;
      padding: 4px 0; font-size: 13px;
    }
    .drawer .detail-label { color: var(--secondary-text-color); }
    .drawer .detail-value {
      font-family: var(--ha-font-family-code, monospace); font-size: 12px;
      color: var(--primary-text-color); max-width: 60%; text-align: right; word-break: break-all;
    }
    .drawer .entity-row {
      padding: 6px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); font-size: 13px;
    }
    .drawer .entity-row:last-child { border-bottom: none; }
  `,l([m({attribute:!1})],_.prototype,"hass",2),l([m({type:Number})],_.prototype,"refreshKey",2),l([m({type:String})],_.prototype,"miniserverId",2),l([p()],_.prototype,"_devices",2),l([p()],_.prototype,"_filter",2),l([p()],_.prototype,"_filterDomain",2),l([p()],_.prototype,"_filterRoom",2),l([p()],_.prototype,"_filterStatus",2),l([p()],_.prototype,"_loading",2),l([p()],_.prototype,"_error",2),l([p()],_.prototype,"_sortKey",2),l([p()],_.prototype,"_sortDir",2),l([p()],_.prototype,"_detail",2),l([p()],_.prototype,"_detailLoading",2),_=l([y("devices-view")],_);var w=class extends f{constructor(){super(...arguments);this.refreshKey=0;this._rooms=[];this._haAreas=[];this._loading=!0;this._syncing=!1;this._error="";this._message=""}connectedCallback(){super.connectedCallback(),this._load()}updated(e){e.has("refreshKey")&&e.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let e=await Ue(this.hass,this.miniserverId);this._rooms=e.rooms,this._haAreas=e.ha_areas}catch(e){this._error=e instanceof Error?e.message:String(e)}finally{this._loading=!1}}async _syncAreas(e){this._syncing=!0,this._message="",this._error="";try{await Ne(this.hass),await Pe(this.hass,e),this._message=e?"Synced areas and created missing ones.":"Synced devices to existing areas.",S(this,this._message),await this._load()}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._syncing=!1}}render(){if(this._loading)return a`<p class="status">Loading areas…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let e=this._rooms.filter(r=>r.ha_area_id).length,t=this._rooms.length;return a`
      <p class="page-intro">
        Maps Loxone rooms to Home Assistant areas.
        <em>Sync to existing areas</em> links rooms to HA areas by name;
        <em>Sync and create</em> also creates new HA areas for any unmatched rooms.
        After syncing, assign devices to areas via the HA device registry.
      </p>
      <div class="toolbar">
        <button
          ?disabled=${this._syncing}
          @click=${()=>this._syncAreas(!1)}
        >
          Sync to existing areas
        </button>
        <button
          class="secondary"
          ?disabled=${this._syncing}
          @click=${()=>this._syncAreas(!0)}
        >
          Sync + create missing areas
        </button>
      </div>
      ${this._message?a`<p class="message">${this._message}</p>`:""}
      <p class="summary">
        <span class="count">${e}</span> / ${t} Loxone rooms mapped to
        HA areas
      </p>
      <table>
        <thead>
          <tr>
            <th>Loxone Room</th>
            <th>HA Area</th>
            <th>Devices</th>
          </tr>
        </thead>
        <tbody>
          ${this._rooms.map(r=>a`
              <tr>
                <td>${r.name}</td>
                <td>
                  ${r.ha_area_name?a`<span class="mapped">${r.ha_area_name}</span>`:a`<span class="unmapped">Not mapped</span>`}
                </td>
                <td>${r.device_count}</td>
              </tr>
            `)}
        </tbody>
      </table>
    `}};w.styles=x`
    :host {
      display: block;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    button {
      padding: 8px 16px;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      transition: opacity 0.2s;
    }
    button:hover {
      opacity: 0.85;
    }
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    button.secondary {
      background: var(--divider-color, #e0e0e0);
      color: var(--primary-text-color, #212121);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    th {
      text-align: left;
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    td {
      padding: 10px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    tr:last-child td {
      border-bottom: none;
    }
    .mapped {
      color: var(--success-color, #4caf50);
      font-weight: 500;
    }
    .unmapped {
      color: var(--warning-color, #ff9800);
    }
    .status {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 16px;
    }
    .error {
      color: var(--error-color, #db4437);
    }
    .message {
      color: var(--success-color, #4caf50);
      font-size: 13px;
      margin-bottom: 8px;
    }
    .summary {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin-bottom: 8px;
    }
    .count {
      font-weight: 500;
      color: var(--primary-color, #03a9f4);
    }
  `,l([m({attribute:!1})],w.prototype,"hass",2),l([m({type:Number})],w.prototype,"refreshKey",2),l([m({type:String})],w.prototype,"miniserverId",2),l([p()],w.prototype,"_rooms",2),l([p()],w.prototype,"_haAreas",2),l([p()],w.prototype,"_loading",2),l([p()],w.prototype,"_syncing",2),l([p()],w.prototype,"_error",2),l([p()],w.prototype,"_message",2),w=l([y("areas-view")],w);var vt=["cover","sensor","binary_sensor","switch","light","number","input_boolean","input_number"],ft=["uuid_up_vo","uuid_down_vo","uuid_target_vo"],bt={uuid_up_vo:"Move-up VO",uuid_down_vo:"Move-down VO",uuid_target_vo:"Target position VO"};function xt(i,o,e,t){return{uuid_up_vo:`Switch VO \u2014 connect to ${i}'s "${o}" output`,uuid_down_vo:`Switch VO \u2014 connect to ${i}'s "${e}" output`,uuid_target_vo:`Slider VO \u2014 connect to ${i}'s "${t}" output`}}var b=class extends f{constructor(){super(...arguments);this.refreshKey=0;this._bridges=[];this._devices=[];this._loading=!0;this._error="";this._message="";this._newEntityId="";this._newLoxoneUuid="";this._entityFilter="";this._loxoneFilter="";this._showEntityDropdown=!1;this._showLoxoneDropdown=!1;this._tableFilter="";this._confirmRemove=null;this._coverVoUuids={uuid_up_vo:"",uuid_down_vo:"",uuid_target_vo:""};this._coverGuideOpen=!1}connectedCallback(){super.connectedCallback(),this._load()}updated(e){e.has("refreshKey")&&e.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[e,t]=await Promise.all([Ke(this.hass,this.miniserverId),K(this.hass,this.miniserverId)]);this._bridges=e.bridges,this._devices=t.devices}catch(e){this._error=e instanceof Error?e.message:String(e)}finally{this._loading=!1}}get _availableEntities(){let e=new Set(this._bridges.map(s=>s.entity_id)),t=new Set;for(let s of this._devices)for(let n of s.ha_entities)t.add(n.entity_id);let r=[];for(let[s,n]of Object.entries(this.hass.states)){let c=s.split(".")[0];vt.includes(c)&&(t.has(s)||e.has(s)||r.push({entity_id:s,friendly_name:n.attributes.friendly_name||"",domain:c}))}return r.sort((s,n)=>s.domain!==n.domain?s.domain.localeCompare(n.domain):s.entity_id.localeCompare(n.entity_id)),r}get _filteredEntities(){if(!this._entityFilter)return this._availableEntities;let e=this._entityFilter.toLowerCase();return this._availableEntities.filter(t=>t.entity_id.toLowerCase().includes(e)||t.friendly_name.toLowerCase().includes(e))}_groupByKey(e,t){let r=new Map;for(let s of e){let n=t(s),c=r.get(n)||[];c.push(s),r.set(n,c)}return r}get _availableLoxoneControls(){let e=new Set(this._bridges.map(r=>r.loxone_uuid)),t=[];for(let r of this._devices)e.has(r.uuid)||t.push({uuid:r.uuid,name:r.name,type:r.type,room:r.room||"\u2014"});return t.sort((r,s)=>r.room!==s.room?r.room.localeCompare(s.room):r.name.localeCompare(s.name)),t}get _filteredLoxoneControls(){if(!this._loxoneFilter)return this._availableLoxoneControls;let e=this._loxoneFilter.toLowerCase();return this._availableLoxoneControls.filter(t=>t.name.toLowerCase().includes(e)||t.type.toLowerCase().includes(e)||t.room.toLowerCase().includes(e))}_onEntityFocus(){this._showEntityDropdown=!0}_onEntityBlur(){setTimeout(()=>{this._showEntityDropdown=!1},200)}_selectEntity(e){this._newEntityId=e,this._entityFilter=e,this._showEntityDropdown=!1,e.startsWith("cover.")||this._resetCoverVos()}_onLoxoneFocus(){this._showLoxoneDropdown=!0}_onLoxoneBlur(){setTimeout(()=>{this._showLoxoneDropdown=!1},200)}_selectLoxone(e,t){this._newLoxoneUuid=e,this._loxoneFilter=t,this._showLoxoneDropdown=!1}get _isCoverEntity(){return this._newEntityId.startsWith("cover.")}get _coverNamePrefix(){return this._newEntityId.replace(/^cover\./,"").replace(/_/g," ").split(" ").map(t=>t.charAt(0).toUpperCase()+t.slice(1)).join("_")}get _coverDeviceClass(){return this.hass.states[this._newEntityId]?.attributes.device_class??""}get _loxoneBlockName(){return this._coverDeviceClass==="window"?{block:"Window (Fenster)",upLabel:"open",downLabel:"close",posLabel:"position"}:{block:"Jalousie",upLabel:"up",downLabel:"down",posLabel:"manualPosition"}}_scanLoxoneForCover(){let e=this._coverNamePrefix.toLowerCase(),t={...this._coverVoUuids},r=!1;for(let s of this._devices){let n=s.name.toLowerCase();!r&&n.includes(e)&&n.includes("position")&&(this._newLoxoneUuid=s.uuid,this._loxoneFilter=s.name,r=!0),!t.uuid_up_vo&&n.includes(e)&&n.includes("up")&&(t.uuid_up_vo=s.uuid),!t.uuid_down_vo&&n.includes(e)&&n.includes("down")&&(t.uuid_down_vo=s.uuid),!t.uuid_target_vo&&n.includes(e)&&n.includes("target")&&(t.uuid_target_vo=s.uuid)}this._coverVoUuids=t,this._message=r?"Scan complete \u2014 matched controls pre-filled. Verify before saving.":"Scan found no matching controls. Create them in Loxone Config first (see setup guide)."}_resetCoverVos(){this._coverVoUuids={uuid_up_vo:"",uuid_down_vo:"",uuid_target_vo:""},this._coverGuideOpen=!1}get _filteredBridges(){if(!this._tableFilter)return this._bridges;let e=this._tableFilter.toLowerCase();return this._bridges.filter(t=>t.entity_id.toLowerCase().includes(e)||(t.loxone_name||"").toLowerCase().includes(e)||t.loxone_type.toLowerCase().includes(e))}async _addBridge(){if(!(!this._newEntityId||!this._newLoxoneUuid)){this._error="",this._message="";try{let e=this._isCoverEntity?Object.fromEntries(Object.entries(this._coverVoUuids).filter(([,t])=>t!=="")):void 0;await Be(this.hass,this._newEntityId,this._newLoxoneUuid,this.miniserverId,e),S(this,`Bridge added: ${this._newEntityId}`),this._message=`Bridge added: ${this._newEntityId}`,this._newEntityId="",this._newLoxoneUuid="",this._entityFilter="",this._loxoneFilter="",this._resetCoverVos(),await this._load()}catch(e){this._error=e instanceof Error?e.message:String(e)}}}_requestRemove(e){this._confirmRemove=e}async _confirmAndRemove(){let e=this._confirmRemove;if(e){this._confirmRemove=null,this._error="",this._message="";try{await Ge(this.hass,e,this.miniserverId),S(this,`Bridge removed: ${e}`),this._message=`Bridge removed: ${e}`,await this._load()}catch(t){this._error=t instanceof Error?t.message:String(t)}}}render(){if(this._loading)return a`<p class="status">Loading bridges…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let e=this._filteredEntities,t=this._groupByKey(e,n=>n.domain),r=this._filteredLoxoneControls,s=this._groupByKey(r,n=>n.room);return a`
      <p class="page-intro">
        Links a Home Assistant entity to a Loxone virtual output (VO) so state changes
        flow bidirectionally. Useful for integrating third-party devices — KNX, KLF200 covers,
        Z-Wave switches — with Loxone without native support. Cover entities get extra
        VO pickers for up/down/position controls.
      </p>
      <div class="add-form">
        <div class="field">
          <label>HA Entity</label>
          <div class="combo-wrapper">
            <input
              type="text"
              placeholder="Search entities…"
              .value=${this._entityFilter}
              @input=${n=>{this._entityFilter=n.target.value,this._newEntityId=this._entityFilter,this._showEntityDropdown=!0}}
              @focus=${this._onEntityFocus}
              @blur=${this._onEntityBlur}
              autocomplete="off"
            />
            ${this._showEntityDropdown?a`
                  <div class="combo-dropdown">
                    ${e.length===0?a`<div class="combo-empty">No matching entities</div>`:Array.from(t.entries()).map(([n,c])=>a`
                            <div class="combo-group">${n}</div>
                            ${c.map(d=>a`
                                <div
                                  class="combo-option"
                                  @mousedown=${u=>{u.preventDefault(),this._selectEntity(d.entity_id)}}
                                >
                                  <span>${d.entity_id}</span>
                                  ${d.friendly_name?a`<span class="secondary"
                                        >${d.friendly_name}</span
                                      >`:""}
                                </div>
                              `)}
                          `)}
                  </div>
                `:""}
          </div>
        </div>
        <div class="field">
          <label>Loxone Control</label>
          <div class="combo-wrapper">
            <input
              type="text"
              placeholder="Search controls…"
              .value=${this._loxoneFilter}
              @input=${n=>{this._loxoneFilter=n.target.value,this._newLoxoneUuid="",this._showLoxoneDropdown=!0}}
              @focus=${this._onLoxoneFocus}
              @blur=${this._onLoxoneBlur}
              autocomplete="off"
            />
            ${this._showLoxoneDropdown?a`
                  <div class="combo-dropdown">
                    ${r.length===0?a`<div class="combo-empty">No matching controls</div>`:Array.from(s.entries()).map(([n,c])=>a`
                            <div class="combo-group">${n}</div>
                            ${c.map(d=>a`
                                <div
                                  class="combo-option"
                                  @mousedown=${u=>{u.preventDefault(),this._selectLoxone(d.uuid,d.name)}}
                                >
                                  <span>${d.name}</span>
                                  <span class="secondary">${d.type}</span>
                                </div>
                              `)}
                          `)}
                  </div>
                `:""}
          </div>
        </div>
        <button @click=${this._addBridge} ?disabled=${!this._newEntityId||!this._newLoxoneUuid}>Add Bridge</button>
      </div>

      ${this._isCoverEntity?a`
        <div class="cover-section">
          <h4>${this._coverDeviceClass==="window"?"Window":"Cover"} Bridge — optional VO controls</h4>
          ${(()=>{let{block:n,upLabel:c,downLabel:d,posLabel:u}=this._loxoneBlockName,h=xt(n,c,d,u);return a`
              <div class="cover-vo-grid">
                ${ft.map(g=>a`
                  <div class="cover-vo-field">
                    <label>${bt[g]} <em style="font-weight:normal">(optional)</em></label>
                    <input
                      type="text"
                      placeholder="Paste UUID or use Scan…"
                      .value=${this._coverVoUuids[g]}
                      @input=${$=>{this._coverVoUuids={...this._coverVoUuids,[g]:$.target.value.trim()}}}
                    />
                    <span class="hint">${h[g]}</span>
                  </div>
                `)}
              </div>
            `})()}

          <div class="cover-actions">
            <button class="secondary" @click=${this._scanLoxoneForCover}>
              🔍 Scan Loxone for matching controls
            </button>
          </div>

          ${(()=>{let{block:n,upLabel:c,downLabel:d,posLabel:u}=this._loxoneBlockName,h=this._coverNamePrefix;return a`
              <details class="cover-guide" ?open=${this._coverGuideOpen}
                @toggle=${g=>{this._coverGuideOpen=g.target.open}}>
                <summary>Loxone Config setup guide — <em>${n}</em></summary>
                <ol>
                  <li>
                    Create a <strong>Slider Virtual Input</strong> (Virtueller Eingang, analog, 0–100) named
                    <code>${h}_Position</code>
                    — PyLoxone writes the actual position here so Loxone always knows where it is.
                  </li>
                  <li>
                    (Optional) Create a <strong>Slider Virtual Output</strong> (Virtueller Ausgang, analog) named
                    <code>${h}_Target</code>
                    — connect to the <em>${n}</em>'s <em>${u}</em> output.
                    PyLoxone subscribes to this and calls <code>set_cover_position</code>.
                  </li>
                  <li>
                    (Optional) Create a <strong>Switch Virtual Output</strong> named
                    <code>${h}_Up</code>
                    — connect to the <em>${n}</em>'s <em>${c}</em> output (drives 1 when opening).
                    PyLoxone calls <code>open_cover</code>.
                  </li>
                  <li>
                    (Optional) Create a <strong>Switch Virtual Output</strong> named
                    <code>${h}_Down</code>
                    — connect to the <em>${n}</em>'s <em>${d}</em> output (drives 1 when closing).
                    PyLoxone calls <code>close_cover</code>.
                  </li>
                  <li>
                    Deploy Loxone Config to the Miniserver, then use
                    <strong>🔍 Scan Loxone</strong> above to auto-fill the UUID fields,
                    or paste the UUIDs from the Loxone Config device tree manually.
                  </li>
                </ol>
              </details>
            `})()}
        </div>
      `:""}
      ${this._message?a`<p class="message">${this._message}</p>`:""}
      ${this._bridges.length>0?a`
        <p class="summary"><span class="count">${this._bridges.length}</span> bridge${this._bridges.length!==1?"s":""} configured</p>
        <div class="table-toolbar">
          <input type="text" placeholder="Search bridges…"
            .value=${this._tableFilter}
            @input=${n=>{this._tableFilter=n.target.value}} />
        </div>
      `:""}
      ${this._bridges.length===0?a`<p class="empty">No device bridges configured.</p>`:(()=>{let n=this._filteredBridges,c=this._groupByKey(n,d=>d.entity_id.split(".")[0]);return a`
              <table>
                <thead>
                  <tr>
                    <th>HA Entity</th>
                    <th>State</th>
                    <th></th>
                    <th>Loxone Control</th>
                    <th>Type</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  ${Array.from(c.entries()).map(([d,u])=>a`
                    <tr class="group-label"><td colspan="6">${d} (${u.length})</td></tr>
                    ${u.map(h=>{let g=this.hass.states[h.entity_id],$=g?g.state:"unavailable",R=!g||$==="unavailable"||$==="unknown"?"state-warn":"";return a`
                        <tr>
                          <td>${h.entity_id}</td>
                          <td><span class="state-value ${R}">${$}</span></td>
                          <td class="direction">→</td>
                          <td>${h.loxone_name||h.loxone_uuid}</td>
                          <td><span class="badge">${h.loxone_type}</span></td>
                          <td><button class="danger" @click=${()=>this._requestRemove(h.entity_id)}>Remove</button></td>
                        </tr>
                      `})}
                  `)}
                </tbody>
              </table>
            `})()}
      ${this._confirmRemove?a`
        <div class="confirm-overlay" @click=${()=>{this._confirmRemove=null}}>
          <div class="confirm-dialog" @click=${n=>n.stopPropagation()}>
            <h3>Remove bridge?</h3>
            <p>This will remove the bridge for <strong>${this._confirmRemove}</strong>. The entity will no longer be bridged to its Loxone control.</p>
            <div class="actions">
              <button class="secondary" @click=${()=>{this._confirmRemove=null}}>Cancel</button>
              <button class="danger" @click=${this._confirmAndRemove}>Remove</button>
            </div>
          </div>
        </div>
      `:""}
    `}};b.styles=x`
    :host {
      display: block;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .add-form {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: flex-end;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      min-width: 240px;
    }
    .field label {
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
    }
    input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      width: 100%;
      box-sizing: border-box;
    }
    .combo-wrapper {
      position: relative;
    }
    .combo-dropdown {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      max-height: 260px;
      overflow-y: auto;
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 0 0 8px 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 10;
      margin-top: -1px;
    }
    .combo-group {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      padding: 8px 12px 4px;
      background: var(--primary-background-color, #fafafa);
    }
    .combo-option {
      padding: 8px 12px;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .combo-option:hover {
      background: var(--primary-color, #03a9f4);
      color: #fff;
    }
    .combo-option .secondary {
      color: var(--secondary-text-color, #727272);
      font-size: 12px;
      margin-left: 8px;
      flex-shrink: 0;
    }
    .combo-option:hover .secondary {
      color: rgba(255, 255, 255, 0.8);
    }
    .combo-empty {
      padding: 12px;
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      text-align: center;
    }
    button {
      padding: 8px 16px;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      transition: opacity 0.2s;
      white-space: nowrap;
    }
    button:hover {
      opacity: 0.85;
    }
    button.danger {
      background: var(--error-color, #db4437);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    th {
      text-align: left;
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    td {
      padding: 10px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    tr:last-child td {
      border-bottom: none;
    }
    .state-value {
      font-family: var(--ha-font-family-code, monospace);
      font-size: 13px;
      padding: 2px 8px;
      border-radius: 8px;
      background: var(--success-color, #4caf50);
      color: #fff;
    }
    .state-value.state-warn {
      background: var(--warning-color, #ff9800);
    }
    .direction {
      text-align: center;
      font-size: 18px;
      color: var(--secondary-text-color, #727272);
      padding-left: 4px;
      padding-right: 4px;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 500;
      background: var(--divider-color, #e0e0e0);
      color: var(--secondary-text-color, #727272);
    }
    .status {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 16px;
    }
    .error {
      color: var(--error-color, #db4437);
    }
    .message {
      color: var(--success-color, #4caf50);
      font-size: 13px;
      margin-bottom: 8px;
    }
    .empty {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 24px;
      text-align: center;
    }
    .table-toolbar {
      display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;
    }
    .table-toolbar input {
      padding: 8px 12px; border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px; background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121); flex: 1; min-width: 180px; max-width: 350px;
    }
    .summary { font-size: 13px; color: var(--secondary-text-color, #727272); margin-bottom: 12px; }
    .summary .count { font-weight: 500; color: var(--primary-color, #03a9f4); }
    .group-label td {
      padding: 8px 16px; font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.5px; color: var(--secondary-text-color, #727272);
      background: var(--table-header-background-color, var(--primary-background-color, #fafafa));
    }
    .cover-section {
      margin-top: 12px;
      padding: 12px 16px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      background: var(--primary-background-color, #fafafa);
    }
    .cover-section h4 {
      margin: 0 0 10px 0;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
    }
    .cover-vo-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 10px;
    }
    .cover-vo-field {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .cover-vo-field label {
      font-size: 11px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
    }
    .cover-vo-field .hint {
      font-size: 10px;
      color: var(--disabled-text-color, #9e9e9e);
      font-style: italic;
    }
    .cover-guide {
      margin-top: 10px;
      padding: 10px 12px;
      background: var(--card-background-color, #fff);
      border-radius: 6px;
      border: 1px solid var(--divider-color, #e0e0e0);
      font-size: 12px;
    }
    .cover-guide summary {
      cursor: pointer;
      font-weight: 500;
      color: var(--primary-color, #03a9f4);
      user-select: none;
    }
    .cover-guide ol {
      margin: 8px 0 0 0;
      padding-left: 18px;
      line-height: 1.7;
    }
    .cover-guide code {
      font-family: var(--ha-font-family-code, monospace);
      background: var(--primary-background-color, #f5f5f5);
      padding: 1px 5px;
      border-radius: 3px;
      font-size: 11px;
    }
    .cover-actions {
      display: flex;
      gap: 8px;
      margin-top: 10px;
      flex-wrap: wrap;
    }
    button.secondary {
      background: var(--secondary-background-color, #e0e0e0);
      color: var(--primary-text-color, #212121);
    }
    .confirm-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.4); z-index: 100;
      display: flex; align-items: center; justify-content: center;
    }
    .confirm-dialog {
      background: var(--card-background-color, #fff); border-radius: 12px;
      padding: 24px; min-width: 320px; box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    .confirm-dialog h3 { margin: 0 0 12px; font-size: 16px; font-weight: 500; }
    .confirm-dialog p { font-size: 14px; margin: 0 0 20px; color: var(--secondary-text-color); }
    .confirm-dialog .actions { display: flex; gap: 8px; justify-content: flex-end; }
    .confirm-dialog button.secondary {
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
      border: 1px solid var(--divider-color, #e0e0e0);
    }
  `,l([m({attribute:!1})],b.prototype,"hass",2),l([m({type:Number})],b.prototype,"refreshKey",2),l([m({type:String})],b.prototype,"miniserverId",2),l([p()],b.prototype,"_bridges",2),l([p()],b.prototype,"_devices",2),l([p()],b.prototype,"_loading",2),l([p()],b.prototype,"_error",2),l([p()],b.prototype,"_message",2),l([p()],b.prototype,"_newEntityId",2),l([p()],b.prototype,"_newLoxoneUuid",2),l([p()],b.prototype,"_entityFilter",2),l([p()],b.prototype,"_loxoneFilter",2),l([p()],b.prototype,"_showEntityDropdown",2),l([p()],b.prototype,"_showLoxoneDropdown",2),l([p()],b.prototype,"_tableFilter",2),l([p()],b.prototype,"_confirmRemove",2),l([p()],b.prototype,"_coverVoUuids",2),l([p()],b.prototype,"_coverGuideOpen",2),b=l([y("bridges-view")],b);var A=class extends f{constructor(){super(...arguments);this.refreshKey=0;this._status=null;this._diff=null;this._loading=!0;this._error=""}connectedCallback(){super.connectedCallback(),this._load()}updated(e){e.has("refreshKey")&&e.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[e,t]=await Promise.all([Fe(this.hass,this.miniserverId),je(this.hass,this.miniserverId).catch(()=>null)]);this._status=e,this._diff=t}catch(e){this._error=e instanceof Error?e.message:String(e)}finally{this._loading=!1}}render(){if(this._loading)return a`<p class="status">Loading status…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;if(!this._status)return a`<p class="status">No status available.</p>`;let e=this._status,t=e.connection_state==="connected"?"conn-connected":e.connection_state==="reconnecting"?"conn-reconnecting":"conn-disconnected",r=e.entities_without_state.length;return a`
      <p class="page-intro">
        Miniserver connection state, firmware details, and entity counts at a glance.
        The <em>Structure diff</em> section shows controls added, removed, or renamed
        since the last structure sync — use it to decide when to re-run the integration setup.
        <em>Entities without state</em> are enabled entities that have never received a
        value from the Miniserver.
      </p>
      <div class="grid">
        <div class="card">
          <h3 class="card-title">Connection</h3>
          <div class="info-row">
            <span class="info-label">Status</span>
            <span class="conn-badge ${t}">${e.connection_state}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Host</span>
            <span class="info-value">${e.host}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Miniserver</span>
            <span class="info-value"
              >${e.miniserver_name||"\u2014"}</span
            >
          </div>
          <div class="info-row">
            <span class="info-label">Serial</span>
            <span class="info-value">${e.serial_number||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Type</span>
            <span class="info-value">${e.miniserver_type||"\u2014"}</span>
          </div>
        </div>

        <div class="card">
          <h3 class="card-title">Configuration</h3>
          <div class="info-row">
            <span class="info-label">Firmware</span>
            <span class="info-value">${e.software_version||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Project</span>
            <span class="info-value">${e.project_name||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Location</span>
            <span class="info-value">${e.location||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Controls</span>
            <span class="info-value">${e.controls_count}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Rooms</span>
            <span class="info-value">${e.rooms_count}</span>
          </div>
        </div>
      </div>

      <h3 class="diagnostics-title">Diagnostics</h3>
      <div class="diag-card">
        <div class="diag-item">
          <span class="diag-icon ${e.connection_state==="connected"?"diag-ok":"diag-warn"}"
            >${e.connection_state==="connected"?"\u2713":"\u26A0"}</span
          >
          <div>
            <div class="diag-label">Miniserver connection</div>
            <div class="diag-detail">${e.connection_state}</div>
          </div>
        </div>

        <div class="diag-item">
          <span class="diag-icon ${r===0?"diag-ok":"diag-warn"}"
            >${r===0?"\u2713":"\u26A0"}</span
          >
          <div>
            <div class="diag-label">Entities without state</div>
            <div class="diag-detail">
              ${r===0?`All ${e.entities_enabled} enabled entities have state`:a`${r} of ${e.entities_enabled} enabled
                    entities missing state:
                    <br />
                    ${e.entities_without_state.slice(0,10).join(", ")}${r>10?` \u2026 and ${r-10} more`:""}`}
            </div>
          </div>
        </div>

        ${e.entities_disabled>0?a`
              <div class="diag-item">
                <span class="diag-icon diag-ok">ℹ</span>
                <div>
                  <div class="diag-label">Disabled entities</div>
                  <div class="diag-detail">
                    ${e.entities_disabled} entities disabled (bridged or
                    manually hidden)
                  </div>
                </div>
              </div>
            `:""}

        <div class="diag-item">
          <span class="diag-icon diag-ok">✓</span>
          <div>
            <div class="diag-label">Device bridges</div>
            <div class="diag-detail">
              ${e.bridge_count} bridge${e.bridge_count!==1?"s":""}
              configured
            </div>
          </div>
        </div>

        <div class="diag-item">
          <span class="diag-icon diag-ok">ℹ</span>
          <div>
            <div class="diag-label">Integration summary</div>
            <div class="diag-detail">
              ${e.controls_count} controls across ${e.rooms_count} rooms,
              ${e.entities_total} HA entities (${e.entities_enabled}
              enabled, ${e.entities_disabled} disabled)
            </div>
          </div>
        </div>
      </div>

      ${this._renderStructureDiff()}
      <button class="download-btn" @click=${this._downloadDiagnostics}>⬇ Download Diagnostics</button>
    `}_downloadDiagnostics(){try{let e={status:this._status,structureDiff:this._diff,exported:new Date().toISOString()},t=new Blob([JSON.stringify(e,null,2)],{type:"application/json"}),r=URL.createObjectURL(t),s=document.createElement("a");s.href=r,s.download=`loxone-diagnostics-${new Date().toISOString().slice(0,10)}.json`,document.body.appendChild(s),s.click(),document.body.removeChild(s),URL.revokeObjectURL(r),S(this,"Diagnostics downloaded")}catch{S(this,"Failed to download diagnostics")}}_renderStructureDiff(){let e=this._diff;if(!e||!e.has_diff)return a`
        <h3 class="diagnostics-title" style="margin-top:24px">Structure Changes</h3>
        <div class="diag-card">
          <div class="diag-item">
            <span class="diag-icon diag-ok">✓</span>
            <div>
              <div class="diag-label">No changes detected</div>
              <div class="diag-detail">
                Structure has not changed since the integration was loaded
              </div>
            </div>
          </div>
        </div>
      `;let t=e.added.length+e.removed.length+e.changed.length,r=e.timestamp?new Date(e.timestamp).toLocaleString(this.hass.language||"en"):"Unknown";return a`
      <h3 class="diagnostics-title" style="margin-top:24px">
        Structure Changes
        <span style="font-weight:400;font-size:12px;color:var(--secondary-text-color)">
          — ${t} change${t!==1?"s":""} at ${r}
        </span>
      </h3>
      <div class="diag-card">
        ${e.added.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--success-color,#4caf50)">+</span>
                <div>
                  <div class="diag-label">Added (${e.added.length})</div>
                  <div class="diag-detail">
                    ${e.added.map(s=>a`<div>${s.name} <span style="opacity:0.6">(${s.type})</span> — ${s.room||"no room"}</div>`)}
                  </div>
                </div>
              </div>
            `:""}
        ${e.removed.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--error-color,#db4437)">−</span>
                <div>
                  <div class="diag-label">Removed (${e.removed.length})</div>
                  <div class="diag-detail">
                    ${e.removed.map(s=>a`<div>${s.name} <span style="opacity:0.6">(${s.type})</span> — ${s.room||"no room"}</div>`)}
                  </div>
                </div>
              </div>
            `:""}
        ${e.changed.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--warning-color,#ff9800)">~</span>
                <div>
                  <div class="diag-label">Changed (${e.changed.length})</div>
                  <div class="diag-detail">
                    ${e.changed.map(s=>a`<div>${s.old.name} → ${s.new.name} <span style="opacity:0.6">(${s.new.type})</span></div>`)}
                  </div>
                </div>
              </div>
            `:""}
      </div>
    `}};A.styles=x`
    :host {
      display: block;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    @media (max-width: 800px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
    .card {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    .card-title {
      font-size: 13px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 16px;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .info-row:last-child {
      border-bottom: none;
    }
    .info-label {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
    }
    .info-value {
      font-size: 14px;
      font-weight: 500;
      color: var(--primary-text-color, #212121);
    }
    .conn-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .conn-connected {
      background: var(--success-color, #4caf50);
      color: #fff;
    }
    .conn-reconnecting {
      background: var(--warning-color, #ff9800);
      color: #fff;
    }
    .conn-disconnected {
      background: var(--error-color, #db4437);
      color: #fff;
    }
    .diagnostics-title {
      font-size: 13px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 12px;
    }
    .diag-card {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
    }
    .diag-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .diag-item:last-child {
      border-bottom: none;
    }
    .diag-icon {
      font-size: 18px;
      flex-shrink: 0;
      width: 24px;
      text-align: center;
    }
    .diag-ok {
      color: var(--success-color, #4caf50);
    }
    .diag-warn {
      color: var(--warning-color, #ff9800);
    }
    .diag-label {
      font-size: 14px;
      color: var(--primary-text-color, #212121);
    }
    .diag-detail {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
      margin-top: 2px;
    }
    .status {
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
      padding: 16px;
    }
    .error {
      color: var(--error-color, #db4437);
    }
    .download-btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 8px 16px; border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;
      background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121);
      transition: opacity 0.2s; margin-top: 16px;
    }
    .download-btn:hover { opacity: 0.75; }
  `,l([m({attribute:!1})],A.prototype,"hass",2),l([m({type:Number})],A.prototype,"refreshKey",2),l([m({type:String})],A.prototype,"miniserverId",2),l([p()],A.prototype,"_status",2),l([p()],A.prototype,"_diff",2),l([p()],A.prototype,"_loading",2),l([p()],A.prototype,"_error",2),A=l([y("status-view")],A);var X=500,C=class extends f{constructor(){super(...arguments);this._events=[];this._paused=!1;this._filter="";this._connected=!1;this._error="";this._pendingEvents=[]}connectedCallback(){super.connectedCallback(),this._subscribe()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe()}updated(e){e.has("miniserverId")&&(this._unsubscribe(),this._events=[],this._subscribe())}async _subscribe(){this._error="";try{this._unsub=await this.hass.connection.subscribeMessage(e=>{let t=e;if(t.events){if(this._paused){this._pendingEvents.push(...t.events),this._pendingEvents.length>X&&(this._pendingEvents=this._pendingEvents.slice(-X));return}this._events=[...t.events,...this._events].slice(0,X)}},{type:"loxone/subscribe_events",...this.miniserverId?{miniserver:this.miniserverId}:{}}),this._connected=!0}catch(e){this._error=e instanceof Error?e.message:String(e),this._connected=!1}}_unsubscribe(){this._unsub&&(this._unsub(),this._unsub=void 0),this._connected=!1}_togglePause(){this._paused=!this._paused,!this._paused&&this._pendingEvents.length>0&&(this._events=[...this._pendingEvents,...this._events].slice(0,X),this._pendingEvents=[])}_clear(){this._events=[],this._pendingEvents=[]}_onFilterInput(e){this._filter=e.target.value.toLowerCase()}_formatTime(e){try{return new Date(e).toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:1})}catch{return e}}_formatValue(e){return e==null?"\u2014":typeof e=="number"?Number.isInteger(e)?String(e):e.toFixed(2):typeof e=="object"?JSON.stringify(e):String(e)}render(){let e=this._filter,t=e?this._events.filter(r=>r.name.toLowerCase().includes(e)||r.room.toLowerCase().includes(e)||r.uuid.toLowerCase().includes(e)):this._events;return a`
      <p class="page-intro">
        Live event stream from the Miniserver WebSocket — every state change pushed by
        Loxone appears here in real time. Useful for verifying automations fire, debugging
        timing issues, or finding the UUID of a control by operating it physically.
        Filter by name, room, or UUID. The stream buffers the last ${X} events.
      </p>
      <div class="toolbar">
        <span class="status-dot ${this._connected?"on":"off"}"></span>
        <button
          type="button"
          class="${this._paused?"active":""}"
          aria-pressed=${this._paused?"true":"false"}
          aria-label=${this._paused?"Resume event stream":"Pause event stream"}
          @click=${this._togglePause}
        >
          ${this._paused?"\u25B6 Resume":"\u23F8 Pause"}
        </button>
        <button type="button" @click=${this._clear}>Clear</button>
        <input
          type="text"
          placeholder="Filter by name, room, UUID…"
          .value=${this._filter}
          @input=${this._onFilterInput}
        />
        <span class="count">${t.length} event${t.length!==1?"s":""}</span>
        ${this._error?a`<span class="error">${this._error}</span>`:""}
      </div>
      <div class="log-container">
        ${t.length===0?a`<div class="empty">
              ${this._connected?"Waiting for events\u2026":"Not connected"}
            </div>`:a`
              <div class="scroll-box">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Name</th>
                      <th>Room</th>
                      <th>Value</th>
                      <th>UUID</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${t.map(r=>a`
                        <tr>
                          <td class="ts">${this._formatTime(r.timestamp)}</td>
                          <td class="name">${r.name||"\u2014"}</td>
                          <td class="room">${r.room||"\u2014"}</td>
                          <td class="value">${this._formatValue(r.value)}</td>
                          <td class="uuid" title=${r.uuid}>${r.uuid}</td>
                        </tr>
                      `)}
                  </tbody>
                </table>
              </div>
            `}
      </div>
    `}};C.styles=x`
    :host {
      display: block;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    .toolbar button {
      padding: 6px 16px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
    }
    .toolbar button.active {
      background: var(--primary-color, #03a9f4);
      color: #fff;
      border-color: var(--primary-color, #03a9f4);
    }
    .toolbar input {
      padding: 6px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      flex: 1;
      min-width: 150px;
      max-width: 300px;
    }
    .count {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .status-dot.on {
      background: var(--success-color, #4caf50);
    }
    .status-dot.off {
      background: var(--error-color, #db4437);
    }
    .log-container {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
      overflow: hidden;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    thead {
      position: sticky;
      top: 0;
      z-index: 1;
    }
    th {
      background: var(--primary-color, #03a9f4);
      padding: 10px 12px;
      text-align: left;
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #fff;
      border-bottom: none;
    }
    td {
      padding: 6px 12px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      color: var(--primary-text-color, #212121);
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      font-size: 12px;
    }
    tr:hover td {
      background: var(--table-row-alternative-background-color, #fafafa);
    }
    .ts {
      white-space: nowrap;
      color: var(--secondary-text-color, #727272);
      width: 90px;
    }
    .name { min-width: 120px; }
    .room {
      color: var(--secondary-text-color, #727272);
      min-width: 80px;
    }
    .uuid {
      color: var(--secondary-text-color, #727272);
      font-size: 11px;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .value {
      font-weight: 500;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .scroll-box {
      max-height: 600px;
      overflow-y: auto;
    }
    .empty {
      padding: 24px;
      text-align: center;
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
    }
    .error {
      color: var(--error-color, #db4437);
      font-size: 13px;
    }
  `,l([m({attribute:!1})],C.prototype,"hass",2),l([m({type:String})],C.prototype,"miniserverId",2),l([p()],C.prototype,"_events",2),l([p()],C.prototype,"_paused",2),l([p()],C.prototype,"_filter",2),l([p()],C.prototype,"_connected",2),l([p()],C.prototype,"_error",2),C=l([y("monitor-view")],C);var Ye="loxone_console_history",fe=50,E=class extends f{constructor(){super(...arguments);this._uuid="";this._command="";this._sending=!1;this._history=[];this._devices=[];this._suggestions=[];this._selectedDevice=null}connectedCallback(){super.connectedCallback(),this._loadHistory(),this._loadDevices()}updated(e){e.has("miniserverId")&&this._loadDevices()}_loadHistory(){try{let e=localStorage.getItem(Ye);e&&(this._history=JSON.parse(e))}catch{}}_saveHistory(){try{localStorage.setItem(Ye,JSON.stringify(this._history.slice(-fe)))}catch{}}async _loadDevices(){try{let e=await K(this.hass,this.miniserverId);this._devices=e.devices}catch{}}_onUuidInput(e){this._uuid=e.target.value,this._selectedDevice=null;let t=this._uuid.toLowerCase();t.length>=2?this._suggestions=this._devices.filter(r=>r.name.toLowerCase().includes(t)||r.uuid.toLowerCase().includes(t)||r.type.toLowerCase().includes(t)).slice(0,8):this._suggestions=[]}_selectSuggestion(e){this._uuid=e.uuid,this._selectedDevice=e,this._suggestions=[]}_getCommandHints(){if(!this._selectedDevice)return[];switch(this._selectedDevice.type){case"Switch":return["On","Off","pulse"];case"Dimmer":case"EIBDimmer":return["On","Off","0","50","100"];case"Slider":return["0","50","100"];case"Jalousie":return["up","down","fullUp","fullDown","shade","stop"];case"Gate":return["open","close","stop"];case"LightController":case"LightControllerV2":return["on","off","plus","minus","changeTo/1"];case"IRoomController":case"IRoomControllerV2":return["setComfortTemperature/21","setEcoOffset/2","operatingMode/0"];case"Alarm":return["on","off","delayedOn"];case"ColorPickerV2":return["hsv(0,100,100)","temp(2700,100)"];case"TextInput":return[];default:return["On","Off","pulse"]}}_applyHint(e){this._command=e}_onCommandInput(e){this._command=e.target.value}_onKeyDown(e){e.key==="Enter"&&this._uuid&&this._command&&this._send(),e.key==="Escape"&&(this._suggestions=[])}async _send(){if(!this._uuid||!this._command||this._sending)return;this._sending=!0,this._suggestions=[];let e=new Date().toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),t=this._selectedDevice?.name,r=this._selectedDevice?.uuid||this._uuid;try{let s=await We(this.hass,r,this._command,this.miniserverId);S(this,`Sent "${this._command}" to ${t||r}`),this._history=[...this._history,{uuid:r,name:t,command:this._command,result:"OK",ok:!0,timestamp:e}].slice(-fe)}catch(s){let n=s instanceof Error?s.message:String(s);S(this,`Error: ${n}`),this._history=[...this._history,{uuid:r,name:t,command:this._command,result:n,ok:!1,timestamp:e}].slice(-fe)}finally{this._sending=!1,this._saveHistory()}}_clearHistory(){this._history=[],this._saveHistory()}render(){return a`
      <p class="page-intro">
        Send raw commands directly to a Loxone control by UUID.
        Type a UUID or control name to search, then enter a command string —
        e.g. <code>On</code>, <code>Off</code>, <code>50</code>, or <code>pulse</code>.
        Commands are forwarded over the live WebSocket connection and take effect immediately.
      </p>
      <div class="card">
        <h3 class="card-title">Send Command</h3>
        <div class="form">
          <div class="field">
            <label>UUID / Control</label>
            <input
              type="text"
              placeholder="Type UUID or control name…"
              .value=${this._selectedDevice?this._selectedDevice.name:this._uuid}
              @input=${this._onUuidInput}
              @focus=${()=>{this._selectedDevice&&(this._uuid="",this._selectedDevice=null)}}
              @keydown=${this._onKeyDown}
              @blur=${()=>setTimeout(()=>this._suggestions=[],200)}
            />
            ${this._selectedDevice?a`<div class="selected-label">
                  <span class="sel-uuid">${this._selectedDevice.uuid}</span>
                </div>`:""}
            ${this._suggestions.length>0?a`
                  <div class="suggestions">
                    ${this._suggestions.map(e=>a`
                        <div class="suggestion" @mousedown=${()=>this._selectSuggestion(e)}>
                          <span class="name">${e.name}</span>
                          <span class="type">${e.type}</span>
                        </div>
                      `)}
                  </div>
                `:""}
          </div>
          <div class="field">
            <label>Command</label>
            <input
              type="text"
              placeholder=${this._selectedDevice?`e.g. ${this._getCommandHints()[0]||"value"}`:"On, Off, pulse, 50, \u2026"}
              .value=${this._command}
              @input=${this._onCommandInput}
              @keydown=${this._onKeyDown}
            />
            ${this._getCommandHints().length>0?a`<div class="command-hints">
                  ${this._getCommandHints().map(e=>a`<button class="command-chip" @click=${()=>this._applyHint(e)}>${e}</button>`)}
                </div>`:""}
          </div>
          <button
            class="send"
            ?disabled=${!this._uuid||!this._command||this._sending}
            @click=${this._send}
          >
            ${this._sending?"Sending\u2026":"Send"}
          </button>
        </div>
        <p class="hint">
          Send a raw command to any Loxone control by UUID. Commands are the same
          as WebSocket/HTTP API values: On, Off, pulse, numeric values, etc.
        </p>
      </div>

      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <h3 class="card-title" style="margin:0">History</h3>
          ${this._history.length>0?a`<button
                style="font-size:12px;border:none;background:none;color:var(--secondary-text-color);cursor:pointer;text-decoration:underline"
                @click=${this._clearHistory}
              >Clear</button>`:""}
        </div>
        ${this._history.length===0?a`<div class="empty">No commands sent yet</div>`:a`
              <table class="history-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Control</th>
                    <th>Command</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  ${[...this._history].reverse().map(e=>a`
                      <tr>
                        <td>${e.timestamp}</td>
                        <td>${e.name?a`${e.name} <span class="sel-uuid">${e.uuid}</span>`:e.uuid}</td>
                        <td>${e.command}</td>
                        <td class="${e.ok?"result-ok":"result-err"}">${e.result}</td>
                      </tr>
                    `)}
                </tbody>
              </table>
            `}
      </div>
    `}};E.styles=x`
    :host {
      display: block;
    }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .card {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.1));
      margin-bottom: 16px;
    }
    .card-title {
      font-size: 13px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 16px;
    }
    .form {
      display: flex;
      gap: 8px;
      align-items: flex-end;
      flex-wrap: wrap;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      min-width: 150px;
      position: relative;
    }
    .field label {
      font-size: 12px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .field input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      background: var(--primary-background-color, #fafafa);
      color: var(--primary-text-color, #212121);
    }
    .field input:focus {
      outline: none;
      border-color: var(--primary-color, #03a9f4);
    }
    .suggestions {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 0 0 8px 8px;
      max-height: 200px;
      overflow-y: auto;
      z-index: 10;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .suggestion {
      padding: 6px 12px;
      cursor: pointer;
      font-size: 13px;
      display: flex;
      justify-content: space-between;
    }
    .suggestion:hover {
      background: var(--table-row-alternative-background-color, #f5f5f5);
    }
    .suggestion .name {
      color: var(--primary-text-color, #212121);
    }
    .suggestion .type {
      color: var(--secondary-text-color, #727272);
      font-size: 11px;
    }
    button.send {
      padding: 8px 24px;
      border: none;
      border-radius: 8px;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
    }
    button.send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .history-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    .history-table th {
      padding: 8px 12px;
      text-align: left;
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: var(--primary-color, #03a9f4);
      color: #fff;
      border-bottom: none;
    }
    .history-table td {
      padding: 6px 12px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      font-size: 12px;
    }
    .result-ok { color: var(--success-color, #4caf50); }
    .result-err { color: var(--error-color, #db4437); }
    .empty {
      text-align: center;
      color: var(--secondary-text-color, #727272);
      padding: 16px;
      font-size: 14px;
    }
    .hint {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
      margin-top: 8px;
    }
    .selected-label {
      font-size: 13px;
      color: var(--primary-text-color, #212121);
      margin-top: 4px;
    }
    .selected-label .sel-uuid {
      font-size: 11px;
      color: var(--secondary-text-color, #727272);
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
    }
    .command-hints {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 8px;
    }
    .command-chip {
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      background: var(--secondary-background-color, #e8e8e8);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
      border: none;
      transition: background 0.15s;
    }
    .command-chip:hover {
      background: var(--primary-color, #03a9f4);
      color: #fff;
    }
  `,l([m({attribute:!1})],E.prototype,"hass",2),l([m({type:String})],E.prototype,"miniserverId",2),l([p()],E.prototype,"_uuid",2),l([p()],E.prototype,"_command",2),l([p()],E.prototype,"_sending",2),l([p()],E.prototype,"_history",2),l([p()],E.prototype,"_devices",2),l([p()],E.prototype,"_suggestions",2),l([p()],E.prototype,"_selectedDevice",2),E=l([y("console-view")],E);var se=500,_t={DEBUG:"var(--secondary-text-color, #727272)",INFO:"var(--primary-color, #03a9f4)",WARNING:"var(--warning-color, #ff9800)",ERROR:"var(--error-color, #db4437)",CRITICAL:"var(--error-color, #db4437)"},Xe={DEBUG:10,INFO:20,WARNING:30,ERROR:40,CRITICAL:50},L=class extends f{constructor(){super(...arguments);this._logs=[];this._paused=!1;this._filter="";this._levelFilter="";this._connected=!1;this._error="";this._pending=[]}connectedCallback(){super.connectedCallback(),this._subscribe()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe()}async _subscribe(){this._error="";try{this._unsub=await this.hass.connection.subscribeMessage(e=>{let t=e;if(!t.message)return;let r={name:t.name,level:t.level,message:t.message,timestamp:t.timestamp};if(this._paused){this._pending.push(r),this._pending.length>se&&(this._pending=this._pending.slice(-se));return}this._logs=[r,...this._logs].slice(0,se)},{type:"loxone/subscribe_logs"}),this._connected=!0}catch(e){this._error=e instanceof Error?e.message:String(e),this._connected=!1}}_unsubscribe(){this._unsub&&(this._unsub(),this._unsub=void 0),this._connected=!1}_togglePause(){this._paused=!this._paused,!this._paused&&this._pending.length>0&&(this._logs=[...this._pending.reverse(),...this._logs].slice(0,se),this._pending=[])}_clear(){this._logs=[],this._pending=[]}_formatTime(e){try{return new Date(e*1e3).toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}catch{return String(e)}}_shortName(e){return e.replace(/^custom_components\.loxone\.?/,"")}render(){let e=this._filter.toLowerCase(),t=this._levelFilter,r=this._logs;if(e&&(r=r.filter(s=>s.message.toLowerCase().includes(e)||s.name.toLowerCase().includes(e))),t){let s=Xe[t]??0;r=r.filter(n=>(Xe[n.level]??0)>=s)}return a`
      <p class="page-intro">
        Live log output from all <code>loxone.*</code> loggers, streamed over WebSocket.
        To see <code>DEBUG</code> messages, add <code>custom_components.loxone: debug</code>
        under <code>logger:</code> in your <code>configuration.yaml</code>, then restart.
        Use the level filter to reduce noise, or the text filter to focus on a specific area.
      </p>
      <div class="toolbar">
        <span class="status-dot ${this._connected?"on":"off"}"></span>
        <button
          type="button"
          class="${this._paused?"active":""}"
          aria-pressed=${this._paused?"true":"false"}
          aria-label=${this._paused?"Resume log streaming":"Pause log streaming"}
          @click=${this._togglePause}
        >
          ${this._paused?"\u25B6 Resume":"\u23F8 Pause"}
        </button>
        <button type="button" @click=${this._clear}>Clear</button>
        <input type="text" placeholder="Filter…" .value=${this._filter}
          @input=${s=>{this._filter=s.target.value}} />
        <select .value=${this._levelFilter}
          @change=${s=>{this._levelFilter=s.target.value}}>
          <option value="">All levels</option>
          <option value="DEBUG">DEBUG+</option>
          <option value="INFO">INFO+</option>
          <option value="WARNING">WARNING+</option>
          <option value="ERROR">ERROR+</option>
        </select>
        <span class="count">${r.length} log${r.length!==1?"s":""}</span>
        ${this._error?a`<span class="error">${this._error}</span>`:""}
      </div>
      <p class="hint">Showing warnings and errors by default. For debug/info logs, add <code>custom_components.loxone: debug</code> to your <code>logger:</code> in <code>configuration.yaml</code>.</p>
      <div class="log-container">
        ${r.length===0?a`<div class="empty">${this._connected?"Waiting for log messages\u2026<br>Warnings and errors will appear here.":"Not connected"}</div>`:a`
            <div class="scroll-box">
              ${r.map(s=>a`
                <div class="log-line">
                  <span class="log-ts">${this._formatTime(s.timestamp)}</span>
                  <span class="log-level" style="color:${_t[s.level]||"inherit"}">${s.level}</span>
                  <span class="log-name" title=${s.name}>${this._shortName(s.name)}</span>
                  <span class="log-msg">${s.message}</span>
                </div>
              `)}
            </div>
          `}
      </div>
    `}};L.styles=x`
    :host { display: block; }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .toolbar {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 16px; flex-wrap: wrap;
    }
    .toolbar button {
      padding: 6px 16px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer; font-size: 13px; font-weight: 500;
    }
    .toolbar button.active {
      background: var(--primary-color, #03a9f4);
      color: #fff; border-color: var(--primary-color, #03a9f4);
    }
    .toolbar input {
      padding: 6px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      flex: 1; min-width: 120px; max-width: 300px;
    }
    .toolbar select {
      padding: 6px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
    }
    .count { font-size: 12px; color: var(--secondary-text-color, #727272); }
    .status-dot {
      width: 8px; height: 8px; border-radius: 50%; display: inline-block;
    }
    .status-dot.on { background: var(--success-color, #4caf50); }
    .status-dot.off { background: var(--error-color, #db4437); }
    .log-container {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
      overflow: hidden;
    }
    .scroll-box { max-height: 600px; overflow-y: auto; }
    .log-line {
      padding: 4px 12px; font-size: 12px;
      font-family: var(--ha-font-family-code, "Roboto Mono", monospace);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      display: flex; gap: 8px; align-items: baseline;
    }
    .log-line:hover { background: var(--table-row-alternative-background-color, #fafafa); }
    .log-ts { color: var(--secondary-text-color); white-space: nowrap; min-width: 80px; }
    .log-level {
      font-weight: 600; font-size: 11px; min-width: 55px;
      text-transform: uppercase;
    }
    .log-name { color: var(--secondary-text-color); min-width: 100px; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .log-msg { flex: 1; word-break: break-word; }
    .empty {
      padding: 24px; text-align: center;
      color: var(--secondary-text-color); font-size: 14px;
      line-height: 1.6;
    }
    .hint {
      font-size: 12px; color: var(--secondary-text-color);
      margin-bottom: 12px;
    }
    .hint code {
      background: var(--secondary-background-color, #e8e8e8);
      padding: 1px 5px; border-radius: 4px;
      font-family: var(--ha-font-family-code, monospace);
      font-size: 11px;
    }
    .error { color: var(--error-color, #db4437); font-size: 13px; }
  `,l([m({attribute:!1})],L.prototype,"hass",2),l([p()],L.prototype,"_logs",2),l([p()],L.prototype,"_paused",2),l([p()],L.prototype,"_filter",2),l([p()],L.prototype,"_levelFilter",2),l([p()],L.prototype,"_connected",2),l([p()],L.prototype,"_error",2),L=l([y("logs-view")],L);var k=class extends f{constructor(){super(...arguments);this.refreshKey=0;this._data=null;this._loading=!0;this._error="";this._filter="";this._groupBy="room";this._expanded=new Set}connectedCallback(){super.connectedCallback(),this._load()}updated(e){e.has("refreshKey")&&e.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{this._data=await Je(this.hass,this.miniserverId)}catch(e){this._error=e instanceof Error?e.message:String(e)}finally{this._loading=!1}}_toggle(e){let t=new Set(this._expanded);t.has(e)?t.delete(e):t.add(e),this._expanded=t}_groupControls(e){let t=new Map;for(let r of e){let s=this._groupBy==="room"?r.room||"No room":this._groupBy==="category"?r.category||"No category":r.type,n=t.get(s)||[];n.push(r),t.set(s,n)}return new Map([...t.entries()].sort((r,s)=>r[0].localeCompare(s[0])))}render(){if(this._loading)return a`<p class="status">Loading structure…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;if(!this._data)return a`<p class="status">No data.</p>`;let e=this._data.controls;if(this._filter){let s=this._filter.toLowerCase();e=e.filter(n=>n.name.toLowerCase().includes(s)||n.type.toLowerCase().includes(s)||n.room.toLowerCase().includes(s)||n.uuid.toLowerCase().includes(s))}let t=this._groupControls(e),r=e.reduce((s,n)=>s+n.sub_controls.length,0);return a`
      <p class="page-intro">
        The full control hierarchy from <code>LoxAPP3.json</code> — rooms, categories, controls,
        and their sub-controls with state key names. Use this to find a control's UUID before
        adding a bridge or sending a console command, or to verify what the Miniserver exposes
        after a structure change.
      </p>
      <div class="toolbar">
        <input type="search" placeholder="Search controls…" .value=${this._filter}
          @input=${s=>{this._filter=s.target.value}} />
        <select .value=${this._groupBy}
          @change=${s=>{this._groupBy=s.target.value}}>
          <option value="room">Group by room</option>
          <option value="category">Group by category</option>
          <option value="type">Group by type</option>
        </select>
      </div>
      <p class="summary">
        <span class="count">${e.length}</span> controls,
        <span class="count">${r}</span> sub-controls,
        <span class="count">${this._data.rooms.length}</span> rooms,
        <span class="count">${this._data.categories.length}</span> categories
      </p>
      ${[...t.entries()].map(([s,n])=>{let c=`g_${s}`,d=this._expanded.has(c);return a`
          <div class="group-card">
            <div class="group-header" @click=${()=>this._toggle(c)}>
              <div><span class="arrow">${d?"\u25BC":"\u25B6"}</span>${s}</div>
              <span class="group-count">${n.length}</span>
            </div>
            ${d?n.map(u=>a`
              <div class="ctrl-row">
                <div>
                  <span class="ctrl-name">${u.name}</span>
                  ${u.states.length>0?a`
                    <div class="states-chips">
                      ${u.states.map(h=>a`<span class="state-chip">${h}</span>`)}
                    </div>
                  `:v}
                </div>
                <div class="ctrl-meta">
                  <span class="badge">${u.type}</span>
                  <span style="font-family:var(--ha-font-family-code,monospace);font-size:10px;opacity:0.6"
                        title=${u.uuid}>${u.uuid.slice(0,8)}…</span>
                </div>
              </div>
              ${u.sub_controls.map(h=>a`
                <div class="sub-row">
                  ${h.name} <span class="badge">${h.type}</span>
                  ${h.states.length>0?a`
                    <div class="states-chips">
                      ${h.states.map(g=>a`<span class="state-chip">${g}</span>`)}
                    </div>
                  `:v}
                </div>
              `)}
            `):v}
          </div>
        `})}
    `}};k.styles=x`
    :host { display: block; }
    .page-intro {
      font-size: 13px;
      color: var(--secondary-text-color, #727272);
      margin: 0 0 20px;
      line-height: 1.6;
      max-width: 800px;
    }
    .toolbar {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 16px; flex-wrap: wrap;
    }
    .toolbar input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 14px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      flex: 1; min-width: 200px;
    }
    .toolbar select {
      padding: 8px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px; font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
    }
    .summary {
      font-size: 13px; color: var(--secondary-text-color);
      margin-bottom: 12px;
    }
    .count { font-weight: 500; color: var(--primary-color, #03a9f4); }
    .group-card {
      background: var(--card-background-color, #fff);
      border-radius: 12px; margin-bottom: 12px;
      box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
      overflow: hidden;
    }
    .group-header {
      padding: 12px 16px; cursor: pointer; display: flex;
      justify-content: space-between; align-items: center;
      font-size: 14px; font-weight: 500;
      background: var(--table-header-background-color, var(--card-background-color, #fff));
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      user-select: none;
    }
    .group-header:hover { background: var(--table-row-alternative-background-color, #fafafa); }
    .group-count {
      font-size: 12px; font-weight: 400;
      color: var(--secondary-text-color);
    }
    .arrow { font-size: 10px; margin-right: 8px; }
    .ctrl-row {
      padding: 8px 16px; font-size: 13px;
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
      display: flex; justify-content: space-between; align-items: center;
    }
    .ctrl-row:last-child { border-bottom: none; }
    .ctrl-name { font-weight: 500; }
    .ctrl-meta {
      display: flex; gap: 8px; align-items: center;
      color: var(--secondary-text-color); font-size: 12px;
    }
    .badge {
      display: inline-block; padding: 2px 8px; border-radius: 8px;
      font-size: 11px; font-weight: 500;
      background: var(--divider-color, #e0e0e0);
      color: var(--secondary-text-color);
    }
    .sub-row {
      padding: 4px 16px 4px 32px; font-size: 12px;
      color: var(--secondary-text-color);
      border-bottom: 1px solid var(--divider-color, #e0e0e0);
    }
    .sub-row:last-child { border-bottom: none; }
    .states-chips {
      display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px;
    }
    .state-chip {
      padding: 1px 6px; border-radius: 8px; font-size: 10px;
      background: var(--secondary-background-color, #e8e8e8);
      color: var(--primary-text-color);
    }
    .status { color: var(--secondary-text-color); font-size: 14px; padding: 16px; }
    .error { color: var(--error-color, #db4437); }
  `,l([m({attribute:!1})],k.prototype,"hass",2),l([m({type:Number})],k.prototype,"refreshKey",2),l([m({type:String})],k.prototype,"miniserverId",2),l([p()],k.prototype,"_data",2),l([p()],k.prototype,"_loading",2),l([p()],k.prototype,"_error",2),l([p()],k.prototype,"_filter",2),l([p()],k.prototype,"_groupBy",2),l([p()],k.prototype,"_expanded",2),k=l([y("structure-view")],k);var z=["devices","areas","bridges","monitor","console","logs","structure","status"],Ze="loxone-main-tabpanel";function be(i){return`loxone-tab-${i}`}function Qe(){let i=window.location.hash.replace(/^#/,"").split("?")[0];return z.includes(i)?i:"devices"}var D=class extends f{constructor(){super(...arguments);this._activeTab=Qe();this._refreshKey=0;this._entries=[];this._onHashChange=()=>{this._activeTab=Qe()}}connectedCallback(){super.connectedCallback(),window.addEventListener("hashchange",this._onHashChange),this._loadEntries()}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("hashchange",this._onHashChange)}async _loadEntries(){try{let e=await Oe(this.hass);this._entries=e.entries,!this._selectedMiniserver&&this._entries.length>0&&(this._selectedMiniserver=this._entries[0].miniserver)}catch{}}_setTab(e){this._activeTab=e,window.location.hash=e==="devices"?"":e}_refresh(){this._refreshKey++}_onTabKeydown(e,t){let r=z.indexOf(t);if(r<0)return;let s=null;if(e.key==="ArrowRight"||e.key==="ArrowDown"?s=(r+1)%z.length:e.key==="ArrowLeft"||e.key==="ArrowUp"?s=(r-1+z.length)%z.length:e.key==="Home"?s=0:e.key==="End"&&(s=z.length-1),s===null)return;e.preventDefault();let n=z[s];this._setTab(n),this.updateComplete.then(()=>{this.shadowRoot?.querySelector(`#${be(n)}`)?.focus()})}_onEntryChange(e){let t=e.target;this._selectedMiniserver=t.value,this._refreshKey++}render(){let e=this._entries.length>1;return a`
      <div class="header">
        <div class="header-left">
          <h1>Loxone</h1>
          ${e?a`
                <select
                  class="entry-select"
                  aria-label="Miniserver"
                  .value=${this._selectedMiniserver??""}
                  @change=${this._onEntryChange}
                >
                  ${this._entries.map(t=>a`
                      <option value=${t.miniserver}>
                        ${t.name||t.title||t.host}
                      </option>
                    `)}
                </select>
              `:v}
        </div>
        <button
          type="button"
          class="refresh-btn"
          aria-label="Refresh current view"
          @click=${this._refresh}
        >
          ↻ Refresh
        </button>
      </div>
      <div class="tabs" role="tablist" aria-label="Loxone sections">
        ${z.map(t=>{let r=this._activeTab===t,s=t.charAt(0).toUpperCase()+t.slice(1);return a`
              <button
                type="button"
                role="tab"
                id=${be(t)}
                class="tab ${r?"active":""}"
                aria-selected=${r?"true":"false"}
                aria-controls=${Ze}
                tabindex=${r?0:-1}
                @click=${()=>this._setTab(t)}
                @keydown=${n=>this._onTabKeydown(n,t)}
              >
                ${s}
              </button>
            `})}
      </div>
      <div
        role="tabpanel"
        id=${Ze}
        aria-labelledby=${be(this._activeTab)}
      >
        ${this._renderTab()}
      </div>
    `}_renderTab(){let e=this._refreshKey,t=this._selectedMiniserver;switch(this._activeTab){case"devices":return a`<devices-view .hass=${this.hass} .refreshKey=${e} .miniserverId=${t}></devices-view>`;case"areas":return a`<areas-view .hass=${this.hass} .refreshKey=${e} .miniserverId=${t}></areas-view>`;case"bridges":return a`<bridges-view .hass=${this.hass} .refreshKey=${e} .miniserverId=${t}></bridges-view>`;case"monitor":return a`<monitor-view .hass=${this.hass} .miniserverId=${t}></monitor-view>`;case"console":return a`<console-view .hass=${this.hass} .miniserverId=${t}></console-view>`;case"logs":return a`<logs-view .hass=${this.hass}></logs-view>`;case"structure":return a`<structure-view .hass=${this.hass} .refreshKey=${e} .miniserverId=${t}></structure-view>`;case"status":return a`<status-view .hass=${this.hass} .refreshKey=${e} .miniserverId=${t}></status-view>`}}};D.styles=x`
    :host {
      display: block;
      padding: 24px;
      font-family: var(--ha-font-family, Roboto, sans-serif);
      color: var(--primary-text-color, #212121);
      background: var(--primary-background-color, #fafafa);
      min-height: 100vh;
      box-sizing: border-box;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    h1 {
      font-size: 24px;
      font-weight: 400;
      margin: 0;
    }
    .entry-select {
      padding: 6px 10px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      cursor: pointer;
    }
    .refresh-btn {
      padding: 6px 14px;
      border: 1px solid var(--divider-color, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color, #212121);
      transition: opacity 0.2s;
    }
    .refresh-btn:hover {
      opacity: 0.75;
    }
    .refresh-btn:focus-visible {
      outlineOffset: 2px;
      outline: 2px solid var(--primary-color, #03a9f4);
    }
    .tabs {
      display: flex;
      gap: 0;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--divider-color, #e0e0e0);
      overflow-x: auto;
    }
    .tab {
      margin: 0;
      padding: 10px 20px;
      cursor: pointer;
      font: inherit;
      font-size: 14px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      border: none;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      background: transparent;
      border-radius: 0;
      transition: color 0.2s, border-color 0.2s;
      user-select: none;
      white-space: nowrap;
      appearance: none;
      -webkit-appearance: none;
    }
    .tab:hover {
      color: var(--primary-text-color, #212121);
    }
    .tab.active {
      color: var(--primary-color, #03a9f4);
      border-bottom-color: var(--primary-color, #03a9f4);
    }
    .tab:focus-visible {
      outlineOffset: 2px;
      outline: 2px solid var(--primary-color, #03a9f4);
    }
  `,l([m({attribute:!1})],D.prototype,"hass",2),l([p()],D.prototype,"_activeTab",2),l([p()],D.prototype,"_refreshKey",2),l([p()],D.prototype,"_entries",2),l([p()],D.prototype,"_selectedMiniserver",2),D=l([y("loxone-panel")],D);export{D as LoxonePanel};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
@lit/reactive-element/decorators/custom-element.js:
@lit/reactive-element/decorators/property.js:
@lit/reactive-element/decorators/state.js:
@lit/reactive-element/decorators/event-options.js:
@lit/reactive-element/decorators/base.js:
@lit/reactive-element/decorators/query.js:
@lit/reactive-element/decorators/query-all.js:
@lit/reactive-element/decorators/query-async.js:
@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
