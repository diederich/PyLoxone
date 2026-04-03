var Zt=Object.defineProperty;var Qt=Object.getOwnPropertyDescriptor;var l=(i,e,t,o)=>{for(var r=o>1?void 0:o?Qt(e,t):e,s=i.length-1,n;s>=0;s--)(n=i[s])&&(r=(o?n(e,t,r):n(r))||r);return o&&r&&Zt(e,t,r),r};var Y=globalThis,Z=Y.ShadowRoot&&(Y.ShadyCSS===void 0||Y.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,st=Symbol(),vt=new WeakMap,G=class{constructor(e,t,o){if(this._$cssResult$=!0,o!==st)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(Z&&e===void 0){let o=t!==void 0&&t.length===1;o&&(e=vt.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),o&&vt.set(t,e))}return e}toString(){return this.cssText}},bt=i=>new G(typeof i=="string"?i:i+"",void 0,st),_=(i,...e)=>{let t=i.length===1?i[0]:e.reduce((o,r,s)=>o+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+i[s+1],i[0]);return new G(t,i,st)},_t=(i,e)=>{if(Z)i.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let o=document.createElement("style"),r=Y.litNonce;r!==void 0&&o.setAttribute("nonce",r),o.textContent=t.cssText,i.appendChild(o)}},it=Z?i=>i:i=>i instanceof CSSStyleSheet?(e=>{let t="";for(let o of e.cssRules)t+=o.cssText;return bt(t)})(i):i;var{is:Vt,defineProperty:te,getOwnPropertyDescriptor:ee,getOwnPropertyNames:oe,getOwnPropertySymbols:re,getPrototypeOf:se}=Object,Q=globalThis,xt=Q.trustedTypes,ie=xt?xt.emptyScript:"",ne=Q.reactiveElementPolyfillSupport,B=(i,e)=>i,K={toAttribute(i,e){switch(e){case Boolean:i=i?ie:null;break;case Object:case Array:i=i==null?i:JSON.stringify(i)}return i},fromAttribute(i,e){let t=i;switch(e){case Boolean:t=i!==null;break;case Number:t=i===null?null:Number(i);break;case Object:case Array:try{t=JSON.parse(i)}catch{t=null}}return t}},V=(i,e)=>!Vt(i,e),yt={attribute:!0,type:String,converter:K,reflect:!1,useDefault:!1,hasChanged:V};Symbol.metadata??=Symbol("metadata"),Q.litPropertyMetadata??=new WeakMap;var H=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=yt){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let o=Symbol(),r=this.getPropertyDescriptor(e,o,t);r!==void 0&&te(this.prototype,e,r)}}static getPropertyDescriptor(e,t,o){let{get:r,set:s}=ee(this.prototype,e)??{get(){return this[t]},set(n){this[t]=n}};return{get:r,set(n){let d=r?.call(this);s?.call(this,n),this.requestUpdate(e,d,o)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??yt}static _$Ei(){if(this.hasOwnProperty(B("elementProperties")))return;let e=se(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(B("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(B("properties"))){let t=this.properties,o=[...oe(t),...re(t)];for(let r of o)this.createProperty(r,t[r])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[o,r]of t)this.elementProperties.set(o,r)}this._$Eh=new Map;for(let[t,o]of this.elementProperties){let r=this._$Eu(t,o);r!==void 0&&this._$Eh.set(r,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let o=new Set(e.flat(1/0).reverse());for(let r of o)t.unshift(it(r))}else e!==void 0&&t.push(it(e));return t}static _$Eu(e,t){let o=t.attribute;return o===!1?void 0:typeof o=="string"?o:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let o of t.keys())this.hasOwnProperty(o)&&(e.set(o,this[o]),delete this[o]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return _t(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,o){this._$AK(e,o)}_$ET(e,t){let o=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,o);if(r!==void 0&&o.reflect===!0){let s=(o.converter?.toAttribute!==void 0?o.converter:K).toAttribute(t,o.type);this._$Em=e,s==null?this.removeAttribute(r):this.setAttribute(r,s),this._$Em=null}}_$AK(e,t){let o=this.constructor,r=o._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let s=o.getPropertyOptions(r),n=typeof s.converter=="function"?{fromAttribute:s.converter}:s.converter?.fromAttribute!==void 0?s.converter:K;this._$Em=r;let d=n.fromAttribute(t,s.type);this[r]=d??this._$Ej?.get(r)??d,this._$Em=null}}requestUpdate(e,t,o,r=!1,s){if(e!==void 0){let n=this.constructor;if(r===!1&&(s=this[e]),o??=n.getPropertyOptions(e),!((o.hasChanged??V)(s,t)||o.useDefault&&o.reflect&&s===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,o))))return;this.C(e,t,o)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:o,reflect:r,wrapped:s},n){o&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),s!==!0||n!==void 0)||(this._$AL.has(e)||(this.hasUpdated||o||(t=void 0),this._$AL.set(e,t)),r===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,s]of this._$Ep)this[r]=s;this._$Ep=void 0}let o=this.constructor.elementProperties;if(o.size>0)for(let[r,s]of o){let{wrapped:n}=s,d=this[r];n!==!0||this._$AL.has(r)||d===void 0||this.C(r,void 0,s,d)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(o=>o.hostUpdate?.()),this.update(t)):this._$EM()}catch(o){throw e=!1,this._$EM(),o}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};H.elementStyles=[],H.shadowRootOptions={mode:"open"},H[B("elementProperties")]=new Map,H[B("finalized")]=new Map,ne?.({ReactiveElement:H}),(Q.reactiveElementVersions??=[]).push("2.1.2");var ht=globalThis,$t=i=>i,tt=ht.trustedTypes,wt=tt?tt.createPolicy("lit-html",{createHTML:i=>i}):void 0,Rt="$lit$",z=`lit$${Math.random().toFixed(9).slice(2)}$`,Lt="?"+z,ae=`<${Lt}>`,M=document,F=()=>M.createComment(""),W=i=>i===null||typeof i!="object"&&typeof i!="function",ut=Array.isArray,le=i=>ut(i)||typeof i?.[Symbol.iterator]=="function",nt=`[ 	
\f\r]`,j=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Et=/-->/g,kt=/>/g,T=RegExp(`>|${nt}(?:([^\\s"'>=/]+)(${nt}*=${nt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),St=/'/g,At=/"/g,Dt=/^(?:script|style|textarea|title)$/i,gt=i=>(e,...t)=>({_$litType$:i,strings:e,values:t}),a=gt(1),ye=gt(2),$e=gt(3),P=Symbol.for("lit-noChange"),f=Symbol.for("lit-nothing"),Ct=new WeakMap,I=M.createTreeWalker(M,129);function Ht(i,e){if(!ut(i)||!i.hasOwnProperty("raw"))throw Error("invalid template strings array");return wt!==void 0?wt.createHTML(e):e}var de=(i,e)=>{let t=i.length-1,o=[],r,s=e===2?"<svg>":e===3?"<math>":"",n=j;for(let d=0;d<t;d++){let c=i[d],h,u,g=-1,k=0;for(;k<c.length&&(n.lastIndex=k,u=n.exec(c),u!==null);)k=n.lastIndex,n===j?u[1]==="!--"?n=Et:u[1]!==void 0?n=kt:u[2]!==void 0?(Dt.test(u[2])&&(r=RegExp("</"+u[2],"g")),n=T):u[3]!==void 0&&(n=T):n===T?u[0]===">"?(n=r??j,g=-1):u[1]===void 0?g=-2:(g=n.lastIndex-u[2].length,h=u[1],n=u[3]===void 0?T:u[3]==='"'?At:St):n===At||n===St?n=T:n===Et||n===kt?n=j:(n=T,r=void 0);let L=n===T&&i[d+1].startsWith("/>")?" ":"";s+=n===j?c+ae:g>=0?(o.push(h),c.slice(0,g)+Rt+c.slice(g)+z+L):c+z+(g===-2?d:L)}return[Ht(i,s+(i[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),o]},q=class i{constructor({strings:e,_$litType$:t},o){let r;this.parts=[];let s=0,n=0,d=e.length-1,c=this.parts,[h,u]=de(e,t);if(this.el=i.createElement(h,o),I.currentNode=this.el.content,t===2||t===3){let g=this.el.content.firstChild;g.replaceWith(...g.childNodes)}for(;(r=I.nextNode())!==null&&c.length<d;){if(r.nodeType===1){if(r.hasAttributes())for(let g of r.getAttributeNames())if(g.endsWith(Rt)){let k=u[n++],L=r.getAttribute(g).split(z),X=/([.?@])?(.*)/.exec(k);c.push({type:1,index:s,name:X[2],strings:L,ctor:X[1]==="."?lt:X[1]==="?"?dt:X[1]==="@"?ct:N}),r.removeAttribute(g)}else g.startsWith(z)&&(c.push({type:6,index:s}),r.removeAttribute(g));if(Dt.test(r.tagName)){let g=r.textContent.split(z),k=g.length-1;if(k>0){r.textContent=tt?tt.emptyScript:"";for(let L=0;L<k;L++)r.append(g[L],F()),I.nextNode(),c.push({type:2,index:++s});r.append(g[k],F())}}}else if(r.nodeType===8)if(r.data===Lt)c.push({type:2,index:s});else{let g=-1;for(;(g=r.data.indexOf(z,g+1))!==-1;)c.push({type:7,index:s}),g+=z.length-1}s++}}static createElement(e,t){let o=M.createElement("template");return o.innerHTML=e,o}};function O(i,e,t=i,o){if(e===P)return e;let r=o!==void 0?t._$Co?.[o]:t._$Cl,s=W(e)?void 0:e._$litDirective$;return r?.constructor!==s&&(r?._$AO?.(!1),s===void 0?r=void 0:(r=new s(i),r._$AT(i,t,o)),o!==void 0?(t._$Co??=[])[o]=r:t._$Cl=r),r!==void 0&&(e=O(i,r._$AS(i,e.values),r,o)),e}var at=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:o}=this._$AD,r=(e?.creationScope??M).importNode(t,!0);I.currentNode=r;let s=I.nextNode(),n=0,d=0,c=o[0];for(;c!==void 0;){if(n===c.index){let h;c.type===2?h=new J(s,s.nextSibling,this,e):c.type===1?h=new c.ctor(s,c.name,c.strings,this,e):c.type===6&&(h=new pt(s,this,e)),this._$AV.push(h),c=o[++d]}n!==c?.index&&(s=I.nextNode(),n++)}return I.currentNode=M,r}p(e){let t=0;for(let o of this._$AV)o!==void 0&&(o.strings!==void 0?(o._$AI(e,o,t),t+=o.strings.length-2):o._$AI(e[t])),t++}},J=class i{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,o,r){this.type=2,this._$AH=f,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=o,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=O(this,e,t),W(e)?e===f||e==null||e===""?(this._$AH!==f&&this._$AR(),this._$AH=f):e!==this._$AH&&e!==P&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):le(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==f&&W(this._$AH)?this._$AA.nextSibling.data=e:this.T(M.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:o}=e,r=typeof o=="number"?this._$AC(e):(o.el===void 0&&(o.el=q.createElement(Ht(o.h,o.h[0]),this.options)),o);if(this._$AH?._$AD===r)this._$AH.p(t);else{let s=new at(r,this),n=s.u(this.options);s.p(t),this.T(n),this._$AH=s}}_$AC(e){let t=Ct.get(e.strings);return t===void 0&&Ct.set(e.strings,t=new q(e)),t}k(e){ut(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,o,r=0;for(let s of e)r===t.length?t.push(o=new i(this.O(F()),this.O(F()),this,this.options)):o=t[r],o._$AI(s),r++;r<t.length&&(this._$AR(o&&o._$AB.nextSibling,r),t.length=r)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let o=$t(e).nextSibling;$t(e).remove(),e=o}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},N=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,o,r,s){this.type=1,this._$AH=f,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=s,o.length>2||o[0]!==""||o[1]!==""?(this._$AH=Array(o.length-1).fill(new String),this.strings=o):this._$AH=f}_$AI(e,t=this,o,r){let s=this.strings,n=!1;if(s===void 0)e=O(this,e,t,0),n=!W(e)||e!==this._$AH&&e!==P,n&&(this._$AH=e);else{let d=e,c,h;for(e=s[0],c=0;c<s.length-1;c++)h=O(this,d[o+c],t,c),h===P&&(h=this._$AH[c]),n||=!W(h)||h!==this._$AH[c],h===f?e=f:e!==f&&(e+=(h??"")+s[c+1]),this._$AH[c]=h}n&&!r&&this.j(e)}j(e){e===f?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},lt=class extends N{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===f?void 0:e}},dt=class extends N{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==f)}},ct=class extends N{constructor(e,t,o,r,s){super(e,t,o,r,s),this.type=5}_$AI(e,t=this){if((e=O(this,e,t,0)??f)===P)return;let o=this._$AH,r=e===f&&o!==f||e.capture!==o.capture||e.once!==o.once||e.passive!==o.passive,s=e!==f&&(o===f||r);r&&this.element.removeEventListener(this.name,this,o),s&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},pt=class{constructor(e,t,o){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=o}get _$AU(){return this._$AM._$AU}_$AI(e){O(this,e)}};var ce=ht.litHtmlPolyfillSupport;ce?.(q,J),(ht.litHtmlVersions??=[]).push("3.3.2");var zt=(i,e,t)=>{let o=t?.renderBefore??e,r=o._$litPart$;if(r===void 0){let s=t?.renderBefore??null;o._$litPart$=r=new J(e.insertBefore(F(),s),s,void 0,t??{})}return r._$AI(i),r};var mt=globalThis,v=class extends H{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=zt(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return P}};v._$litElement$=!0,v.finalized=!0,mt.litElementHydrateSupport?.({LitElement:v});var pe=mt.litElementPolyfillSupport;pe?.({LitElement:v});(mt.litElementVersions??=[]).push("4.2.2");var y=i=>(e,t)=>{t!==void 0?t.addInitializer(()=>{customElements.define(i,e)}):customElements.define(i,e)};var he={attribute:!0,type:String,converter:K,reflect:!1,hasChanged:V},ue=(i=he,e,t)=>{let{kind:o,metadata:r}=t,s=globalThis.litPropertyMetadata.get(r);if(s===void 0&&globalThis.litPropertyMetadata.set(r,s=new Map),o==="setter"&&((i=Object.create(i)).wrapped=!0),s.set(t.name,i),o==="accessor"){let{name:n}=t;return{set(d){let c=e.get.call(this);e.set.call(this,d),this.requestUpdate(n,c,i,!0,d)},init(d){return d!==void 0&&this.C(n,void 0,i,d),d}}}if(o==="setter"){let{name:n}=t;return function(d){let c=this[n];e.call(this,d),this.requestUpdate(n,c,i,!0,d)}}throw Error("Unsupported decorator location: "+o)};function m(i){return(e,t)=>typeof t=="object"?ue(i,e,t):((o,r,s)=>{let n=r.hasOwnProperty(s);return r.constructor.createProperty(s,o),n?Object.getOwnPropertyDescriptor(r,s):void 0})(i,e,t)}function p(i){return m({...i,state:!0,attribute:!1})}async function Tt(i){return i.callWS({type:"loxone/list_entries"})}async function U(i,e){return i.callWS({type:"loxone/get_devices",...e?{miniserver:e}:{}})}async function It(i,e,t){return i.callWS({type:"loxone/set_entity_enabled",entity_id:e,enabled:t})}async function Mt(i,e){return i.callWS({type:"loxone/get_areas",...e?{miniserver:e}:{}})}async function Pt(i,e){await i.callService("loxone","sync_areas",{create_areas:e})}async function Ot(i){await i.callService("loxone","sync_device_names")}async function Nt(i,e){return i.callWS({type:"loxone/get_bridges",...e?{miniserver:e}:{}})}async function Ut(i,e,t,o){return i.callWS({type:"loxone/add_bridge",entity_id:e,loxone_uuid:t,...o?{miniserver:o}:{}})}async function Gt(i,e,t){return i.callWS({type:"loxone/remove_bridge",entity_id:e,...t?{miniserver:t}:{}})}async function Bt(i,e){return i.callWS({type:"loxone/get_status",...e?{miniserver:e}:{}})}async function Kt(i,e){return i.callWS({type:"loxone/get_structure_diff",...e?{miniserver:e}:{}})}async function jt(i,e,t,o){return i.callWS({type:"loxone/send_command",uuid:e,command:t,...o?{miniserver:o}:{}})}async function Ft(i,e,t){return i.callWS({type:"loxone/get_control_detail",uuid:e,...t?{miniserver:t}:{}})}async function Wt(i,e){return i.callWS({type:"loxone/get_structure",...e?{miniserver:e}:{}})}function S(i,e){i.dispatchEvent(new CustomEvent("hass-notification",{bubbles:!0,composed:!0,detail:{message:e,duration:4e3}}))}var x=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._devices=[];this._filter="";this._filterDomain="";this._filterRoom="";this._filterStatus="";this._loading=!0;this._error="";this._sortKey="room";this._sortDir="asc";this._detail=null;this._detailLoading=!1}connectedCallback(){super.connectedCallback(),this._loadDevices()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._loadDevices()}async _loadDevices(){this._loading=!0,this._error="";try{let t=await U(this.hass,this.miniserverId);this._devices=t.devices}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}get _allDomains(){let t=new Set;for(let o of this._devices)for(let r of o.ha_entities)t.add(r.entity_id.split(".")[0]);return[...t].sort()}get _allRooms(){let t=new Set;for(let o of this._devices)o.room&&t.add(o.room);return[...t].sort()}get _filteredDevices(){let t=this._devices;if(this._filter){let o=this._filter.toLowerCase();t=t.filter(r=>r.name.toLowerCase().includes(o)||r.type.toLowerCase().includes(o)||r.room.toLowerCase().includes(o)||r.ha_entities.some(s=>s.entity_id.toLowerCase().includes(o)))}if(this._filterDomain){let o=this._filterDomain;t=t.filter(r=>r.ha_entities.some(s=>s.entity_id.startsWith(o+".")))}if(this._filterRoom&&(t=t.filter(o=>o.room===this._filterRoom)),this._filterStatus)switch(this._filterStatus){case"enabled":t=t.filter(o=>o.ha_entities.length>0&&o.ha_entities.some(r=>!r.disabled_by));break;case"disabled":t=t.filter(o=>o.ha_entities.some(r=>!!r.disabled_by));break;case"no-entity":t=t.filter(o=>o.ha_entities.length===0);break}return this._sortDevices(t)}_sortDevices(t){let o=this._sortDir==="asc"?1:-1,r=(h,u)=>{let g=0;switch(this._sortKey){case"name":g=h.name.localeCompare(u.name);break;case"type":g=h.type.localeCompare(u.type)||h.name.localeCompare(u.name);break;case"room":g=(h.room||"").localeCompare(u.room||"")||h.name.localeCompare(u.name);break;case"entities":g=h.ha_entities.length-u.ha_entities.length;break}return g*o},s=new Set(t.filter(h=>!h.parent).map(h=>h.uuid)),n=new Map,d=[];for(let h of t)if(h.parent&&s.has(h.parent)){let u=n.get(h.parent)||[];u.push(h),n.set(h.parent,u)}else d.push(h);d.sort(r);for(let h of n.values())h.sort(r);let c=[];for(let h of d){c.push(h);let u=n.get(h.uuid);u&&c.push(...u)}return c}_toggleSort(t){this._sortKey===t?this._sortDir=this._sortDir==="asc"?"desc":"asc":(this._sortKey=t,this._sortDir="asc")}_sortIndicator(t){return this._sortKey!==t?f:a`<span class="sort-arrow"
      >${this._sortDir==="asc"?"\u25B2":"\u25BC"}</span
    >`}async _openDetail(t){this._detailLoading=!0,this._detail=null;try{this._detail=await Ft(this.hass,t,this.miniserverId)}catch{this._detail=null}finally{this._detailLoading=!1}}_closeDetail(){this._detail=null}async _toggleEntity(t,o){try{await It(this.hass,t,o),S(this,`${t} ${o?"enabled":"disabled"}`),await this._loadDevices()}catch(r){this._error=r instanceof Error?r.message:String(r)}}render(){if(this._loading)return a`<p class="status">Loading devices…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let t=this._filteredDevices,o=new Set(t.map(d=>d.uuid)),r=new Map;for(let d of this._devices)for(let c of d.ha_entities){let h=c.entity_id.split(".")[0];r.set(h,(r.get(h)||0)+1)}let s=[...r.values()].reduce((d,c)=>d+c,0),n=[...r.entries()].sort((d,c)=>c[1]-d[1]).map(([d,c])=>`${c} ${d}`).join(", ");return a`
      <div class="toolbar">
        <input
          type="search"
          placeholder="Filter by name, type, room, or entity…"
          .value=${this._filter}
          @input=${d=>{this._filter=d.target.value}}
        />
        <select class="filter-select" .value=${this._filterDomain}
          @change=${d=>{this._filterDomain=d.target.value}}>
          <option value="">All domains</option>
          ${this._allDomains.map(d=>a`<option value=${d}>${d}</option>`)}
        </select>
        <select class="filter-select" .value=${this._filterRoom}
          @change=${d=>{this._filterRoom=d.target.value}}>
          <option value="">All rooms</option>
          ${this._allRooms.map(d=>a`<option value=${d}>${d}</option>`)}
        </select>
        <select class="filter-select" .value=${this._filterStatus}
          @change=${d=>{this._filterStatus=d.target.value}}>
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
          ${t.map(d=>a`
              <tr class="${d.parent&&o.has(d.parent)?"sub-control":""} clickable"
                  @click=${()=>this._openDetail(d.uuid)}>
                <td>${d.name}</td>
                <td><span class="badge">${d.type}</span></td>
                <td>${d.room||"\u2014"}</td>
                <td>
                  ${d.ha_entities.length===0?a`<span style="color: var(--secondary-text-color)"
                        >—</span
                      >`:d.ha_entities.map(c=>a`
                          <span
                            class="entity-chip ${c.disabled_by?"disabled":""}"
                          >
                            ${c.entity_id}
                            <button
                              class="toggle-btn"
                              title=${c.disabled_by?"Enable":"Disable"}
                              @click=${h=>{h.stopPropagation(),this._toggleEntity(c.entity_id,!!c.disabled_by)}}
                            >
                              ${c.disabled_by?"\u2B1A":"\u2713"}
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
    `}_renderDrawer(t){let o=Object.entries(t.states);return a`
      <div class="drawer-overlay" @click=${this._closeDetail}></div>
      <div class="drawer" @click=${r=>r.stopPropagation()}>
        <button class="close-btn" @click=${this._closeDetail}>✕</button>
        <h2>${t.name}</h2>
        <div class="sub-title">
          <span class="badge">${t.type}</span>
          ${t.room?a` — ${t.room}`:""}
          ${t.category?a` — ${t.category}`:""}
          ${t.is_sub_control&&t.parent_name?a` (sub-control of ${t.parent_name})`:""}
        </div>
        <div class="detail-row">
          <span class="detail-label">UUID</span>
          <span class="detail-value">${t.uuid}</span>
        </div>
        ${o.length>0?a`
          <div class="section-title">States (${o.length})</div>
          ${o.map(([r,s])=>a`
            <div class="detail-row">
              <span class="detail-label">${r}</span>
              <span class="detail-value">${s.value??"\u2014"}${s.last_changed?a` <span style="opacity:0.5;font-size:11px">${new Date(s.last_changed).toLocaleTimeString()}</span>`:""}</span>
            </div>
          `)}
        `:""}
        ${t.ha_entities.length>0?a`
          <div class="section-title">HA Entities (${t.ha_entities.length})</div>
          ${t.ha_entities.map(r=>a`
            <div class="entity-row">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span>${r.entity_id}</span>
                <span class="badge" style="${r.disabled_by?"background:var(--disabled-text-color,#bdbdbd)":"background:var(--success-color,#4caf50);color:#fff"}">${r.disabled_by?"disabled":r.state??"\u2014"}</span>
              </div>
              ${r.last_changed?a`<div style="font-size:11px;color:var(--secondary-text-color);margin-top:2px">Last changed: ${new Date(r.last_changed).toLocaleString()}</div>`:""}
            </div>
          `)}
        `:a`<div class="section-title">No HA entities</div>`}
        ${Object.keys(t.details).length>0?a`
          <div class="section-title">Details</div>
          ${Object.entries(t.details).map(([r,s])=>a`
            <div class="detail-row">
              <span class="detail-label">${r}</span>
              <span class="detail-value">${typeof s=="object"?JSON.stringify(s):String(s)}</span>
            </div>
          `)}
        `:""}
      </div>
    `}};x.styles=_`
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
  `,l([m({attribute:!1})],x.prototype,"hass",2),l([m({type:Number})],x.prototype,"refreshKey",2),l([m({type:String})],x.prototype,"miniserverId",2),l([p()],x.prototype,"_devices",2),l([p()],x.prototype,"_filter",2),l([p()],x.prototype,"_filterDomain",2),l([p()],x.prototype,"_filterRoom",2),l([p()],x.prototype,"_filterStatus",2),l([p()],x.prototype,"_loading",2),l([p()],x.prototype,"_error",2),l([p()],x.prototype,"_sortKey",2),l([p()],x.prototype,"_sortDir",2),l([p()],x.prototype,"_detail",2),l([p()],x.prototype,"_detailLoading",2),x=l([y("devices-view")],x);var $=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._rooms=[];this._haAreas=[];this._loading=!0;this._syncing=!1;this._error="";this._message=""}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let t=await Mt(this.hass,this.miniserverId);this._rooms=t.rooms,this._haAreas=t.ha_areas}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}async _syncAreas(t){this._syncing=!0,this._message="",this._error="";try{await Ot(this.hass),await Pt(this.hass,t),this._message=t?"Synced areas and created missing ones.":"Synced devices to existing areas.",S(this,this._message),await this._load()}catch(o){this._error=o instanceof Error?o.message:String(o)}finally{this._syncing=!1}}render(){if(this._loading)return a`<p class="status">Loading areas…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let t=this._rooms.filter(r=>r.ha_area_id).length,o=this._rooms.length;return a`
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
        <span class="count">${t}</span> / ${o} Loxone rooms mapped to
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
    `}};$.styles=_`
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
  `,l([m({attribute:!1})],$.prototype,"hass",2),l([m({type:Number})],$.prototype,"refreshKey",2),l([m({type:String})],$.prototype,"miniserverId",2),l([p()],$.prototype,"_rooms",2),l([p()],$.prototype,"_haAreas",2),l([p()],$.prototype,"_loading",2),l([p()],$.prototype,"_syncing",2),l([p()],$.prototype,"_error",2),l([p()],$.prototype,"_message",2),$=l([y("areas-view")],$);var ge=["sensor","binary_sensor","switch","light","number","input_boolean","input_number"],b=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._bridges=[];this._devices=[];this._loading=!0;this._error="";this._message="";this._newEntityId="";this._newLoxoneUuid="";this._entityFilter="";this._loxoneFilter="";this._showEntityDropdown=!1;this._showLoxoneDropdown=!1;this._tableFilter="";this._confirmRemove=null}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[t,o]=await Promise.all([Nt(this.hass,this.miniserverId),U(this.hass,this.miniserverId)]);this._bridges=t.bridges,this._devices=o.devices}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}get _availableEntities(){let t=new Set(this._bridges.map(s=>s.entity_id)),o=new Set;for(let s of this._devices)for(let n of s.ha_entities)o.add(n.entity_id);let r=[];for(let[s,n]of Object.entries(this.hass.states)){let d=s.split(".")[0];ge.includes(d)&&(o.has(s)||t.has(s)||r.push({entity_id:s,friendly_name:n.attributes.friendly_name||"",domain:d}))}return r.sort((s,n)=>s.domain!==n.domain?s.domain.localeCompare(n.domain):s.entity_id.localeCompare(n.entity_id)),r}get _filteredEntities(){if(!this._entityFilter)return this._availableEntities;let t=this._entityFilter.toLowerCase();return this._availableEntities.filter(o=>o.entity_id.toLowerCase().includes(t)||o.friendly_name.toLowerCase().includes(t))}_groupByKey(t,o){let r=new Map;for(let s of t){let n=o(s),d=r.get(n)||[];d.push(s),r.set(n,d)}return r}get _availableLoxoneControls(){let t=new Set(this._bridges.map(r=>r.loxone_uuid)),o=[];for(let r of this._devices)t.has(r.uuid)||o.push({uuid:r.uuid,name:r.name,type:r.type,room:r.room||"\u2014"});return o.sort((r,s)=>r.room!==s.room?r.room.localeCompare(s.room):r.name.localeCompare(s.name)),o}get _filteredLoxoneControls(){if(!this._loxoneFilter)return this._availableLoxoneControls;let t=this._loxoneFilter.toLowerCase();return this._availableLoxoneControls.filter(o=>o.name.toLowerCase().includes(t)||o.type.toLowerCase().includes(t)||o.room.toLowerCase().includes(t))}_onEntityFocus(){this._showEntityDropdown=!0}_onEntityBlur(){setTimeout(()=>{this._showEntityDropdown=!1},200)}_selectEntity(t){this._newEntityId=t,this._entityFilter=t,this._showEntityDropdown=!1}_onLoxoneFocus(){this._showLoxoneDropdown=!0}_onLoxoneBlur(){setTimeout(()=>{this._showLoxoneDropdown=!1},200)}_selectLoxone(t,o){this._newLoxoneUuid=t,this._loxoneFilter=o,this._showLoxoneDropdown=!1}get _filteredBridges(){if(!this._tableFilter)return this._bridges;let t=this._tableFilter.toLowerCase();return this._bridges.filter(o=>o.entity_id.toLowerCase().includes(t)||(o.loxone_name||"").toLowerCase().includes(t)||o.loxone_type.toLowerCase().includes(t))}async _addBridge(){if(!(!this._newEntityId||!this._newLoxoneUuid)){this._error="",this._message="";try{await Ut(this.hass,this._newEntityId,this._newLoxoneUuid,this.miniserverId),S(this,`Bridge added: ${this._newEntityId}`),this._message=`Bridge added: ${this._newEntityId}`,this._newEntityId="",this._newLoxoneUuid="",this._entityFilter="",this._loxoneFilter="",await this._load()}catch(t){this._error=t instanceof Error?t.message:String(t)}}}_requestRemove(t){this._confirmRemove=t}async _confirmAndRemove(){let t=this._confirmRemove;if(t){this._confirmRemove=null,this._error="",this._message="";try{await Gt(this.hass,t,this.miniserverId),S(this,`Bridge removed: ${t}`),this._message=`Bridge removed: ${t}`,await this._load()}catch(o){this._error=o instanceof Error?o.message:String(o)}}}render(){if(this._loading)return a`<p class="status">Loading bridges…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let t=this._filteredEntities,o=this._groupByKey(t,n=>n.domain),r=this._filteredLoxoneControls,s=this._groupByKey(r,n=>n.room);return a`
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
                    ${t.length===0?a`<div class="combo-empty">No matching entities</div>`:Array.from(o.entries()).map(([n,d])=>a`
                            <div class="combo-group">${n}</div>
                            ${d.map(c=>a`
                                <div
                                  class="combo-option"
                                  @mousedown=${h=>{h.preventDefault(),this._selectEntity(c.entity_id)}}
                                >
                                  <span>${c.entity_id}</span>
                                  ${c.friendly_name?a`<span class="secondary"
                                        >${c.friendly_name}</span
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
                    ${r.length===0?a`<div class="combo-empty">No matching controls</div>`:Array.from(s.entries()).map(([n,d])=>a`
                            <div class="combo-group">${n}</div>
                            ${d.map(c=>a`
                                <div
                                  class="combo-option"
                                  @mousedown=${h=>{h.preventDefault(),this._selectLoxone(c.uuid,c.name)}}
                                >
                                  <span>${c.name}</span>
                                  <span class="secondary">${c.type}</span>
                                </div>
                              `)}
                          `)}
                  </div>
                `:""}
          </div>
        </div>
        <button @click=${this._addBridge}>Add Bridge</button>
      </div>
      ${this._message?a`<p class="message">${this._message}</p>`:""}
      ${this._bridges.length>0?a`
        <p class="summary"><span class="count">${this._bridges.length}</span> bridge${this._bridges.length!==1?"s":""} configured</p>
        <div class="table-toolbar">
          <input type="text" placeholder="Search bridges…"
            .value=${this._tableFilter}
            @input=${n=>{this._tableFilter=n.target.value}} />
        </div>
      `:""}
      ${this._bridges.length===0?a`<p class="empty">No device bridges configured.</p>`:(()=>{let n=this._filteredBridges,d=this._groupByKey(n,c=>c.entity_id.split(".")[0]);return a`
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
                  ${Array.from(d.entries()).map(([c,h])=>a`
                    <tr class="group-label"><td colspan="6">${c} (${h.length})</td></tr>
                    ${h.map(u=>{let g=this.hass.states[u.entity_id],k=g?g.state:"unavailable",L=!g||k==="unavailable"||k==="unknown"?"state-warn":"";return a`
                        <tr>
                          <td>${u.entity_id}</td>
                          <td><span class="state-value ${L}">${k}</span></td>
                          <td class="direction">→</td>
                          <td>${u.loxone_name||u.loxone_uuid}</td>
                          <td><span class="badge">${u.loxone_type}</span></td>
                          <td><button class="danger" @click=${()=>this._requestRemove(u.entity_id)}>Remove</button></td>
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
    `}};b.styles=_`
    :host {
      display: block;
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
  `,l([m({attribute:!1})],b.prototype,"hass",2),l([m({type:Number})],b.prototype,"refreshKey",2),l([m({type:String})],b.prototype,"miniserverId",2),l([p()],b.prototype,"_bridges",2),l([p()],b.prototype,"_devices",2),l([p()],b.prototype,"_loading",2),l([p()],b.prototype,"_error",2),l([p()],b.prototype,"_message",2),l([p()],b.prototype,"_newEntityId",2),l([p()],b.prototype,"_newLoxoneUuid",2),l([p()],b.prototype,"_entityFilter",2),l([p()],b.prototype,"_loxoneFilter",2),l([p()],b.prototype,"_showEntityDropdown",2),l([p()],b.prototype,"_showLoxoneDropdown",2),l([p()],b.prototype,"_tableFilter",2),l([p()],b.prototype,"_confirmRemove",2),b=l([y("bridges-view")],b);var A=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._status=null;this._diff=null;this._loading=!0;this._error=""}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[t,o]=await Promise.all([Bt(this.hass,this.miniserverId),Kt(this.hass,this.miniserverId).catch(()=>null)]);this._status=t,this._diff=o}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}render(){if(this._loading)return a`<p class="status">Loading status…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;if(!this._status)return a`<p class="status">No status available.</p>`;let t=this._status,o=t.connection_state==="connected"?"conn-connected":t.connection_state==="reconnecting"?"conn-reconnecting":"conn-disconnected",r=t.entities_without_state.length;return a`
      <div class="grid">
        <div class="card">
          <h3 class="card-title">Connection</h3>
          <div class="info-row">
            <span class="info-label">Status</span>
            <span class="conn-badge ${o}">${t.connection_state}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Host</span>
            <span class="info-value">${t.host}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Miniserver</span>
            <span class="info-value"
              >${t.miniserver_name||"\u2014"}</span
            >
          </div>
          <div class="info-row">
            <span class="info-label">Serial</span>
            <span class="info-value">${t.serial_number||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Type</span>
            <span class="info-value">${t.miniserver_type||"\u2014"}</span>
          </div>
        </div>

        <div class="card">
          <h3 class="card-title">Configuration</h3>
          <div class="info-row">
            <span class="info-label">Firmware</span>
            <span class="info-value">${t.software_version||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Project</span>
            <span class="info-value">${t.project_name||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Location</span>
            <span class="info-value">${t.location||"\u2014"}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Controls</span>
            <span class="info-value">${t.controls_count}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Rooms</span>
            <span class="info-value">${t.rooms_count}</span>
          </div>
        </div>
      </div>

      <h3 class="diagnostics-title">Diagnostics</h3>
      <div class="diag-card">
        <div class="diag-item">
          <span class="diag-icon ${t.connection_state==="connected"?"diag-ok":"diag-warn"}"
            >${t.connection_state==="connected"?"\u2713":"\u26A0"}</span
          >
          <div>
            <div class="diag-label">Miniserver connection</div>
            <div class="diag-detail">${t.connection_state}</div>
          </div>
        </div>

        <div class="diag-item">
          <span class="diag-icon ${r===0?"diag-ok":"diag-warn"}"
            >${r===0?"\u2713":"\u26A0"}</span
          >
          <div>
            <div class="diag-label">Entities without state</div>
            <div class="diag-detail">
              ${r===0?`All ${t.entities_enabled} enabled entities have state`:a`${r} of ${t.entities_enabled} enabled
                    entities missing state:
                    <br />
                    ${t.entities_without_state.slice(0,10).join(", ")}${r>10?` \u2026 and ${r-10} more`:""}`}
            </div>
          </div>
        </div>

        ${t.entities_disabled>0?a`
              <div class="diag-item">
                <span class="diag-icon diag-ok">ℹ</span>
                <div>
                  <div class="diag-label">Disabled entities</div>
                  <div class="diag-detail">
                    ${t.entities_disabled} entities disabled (bridged or
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
              ${t.bridge_count} bridge${t.bridge_count!==1?"s":""}
              configured
            </div>
          </div>
        </div>

        <div class="diag-item">
          <span class="diag-icon diag-ok">ℹ</span>
          <div>
            <div class="diag-label">Integration summary</div>
            <div class="diag-detail">
              ${t.controls_count} controls across ${t.rooms_count} rooms,
              ${t.entities_total} HA entities (${t.entities_enabled}
              enabled, ${t.entities_disabled} disabled)
            </div>
          </div>
        </div>
      </div>

      ${this._renderStructureDiff()}
      <button class="download-btn" @click=${this._downloadDiagnostics}>⬇ Download Diagnostics</button>
    `}_downloadDiagnostics(){try{let t={status:this._status,structureDiff:this._diff,exported:new Date().toISOString()},o=new Blob([JSON.stringify(t,null,2)],{type:"application/json"}),r=URL.createObjectURL(o),s=document.createElement("a");s.href=r,s.download=`loxone-diagnostics-${new Date().toISOString().slice(0,10)}.json`,document.body.appendChild(s),s.click(),document.body.removeChild(s),URL.revokeObjectURL(r),S(this,"Diagnostics downloaded")}catch{S(this,"Failed to download diagnostics")}}_renderStructureDiff(){let t=this._diff;if(!t||!t.has_diff)return a`
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
      `;let o=t.added.length+t.removed.length+t.changed.length,r=t.timestamp?new Date(t.timestamp).toLocaleString(this.hass.language||"en"):"Unknown";return a`
      <h3 class="diagnostics-title" style="margin-top:24px">
        Structure Changes
        <span style="font-weight:400;font-size:12px;color:var(--secondary-text-color)">
          — ${o} change${o!==1?"s":""} at ${r}
        </span>
      </h3>
      <div class="diag-card">
        ${t.added.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--success-color,#4caf50)">+</span>
                <div>
                  <div class="diag-label">Added (${t.added.length})</div>
                  <div class="diag-detail">
                    ${t.added.map(s=>a`<div>${s.name} <span style="opacity:0.6">(${s.type})</span> — ${s.room||"no room"}</div>`)}
                  </div>
                </div>
              </div>
            `:""}
        ${t.removed.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--error-color,#db4437)">−</span>
                <div>
                  <div class="diag-label">Removed (${t.removed.length})</div>
                  <div class="diag-detail">
                    ${t.removed.map(s=>a`<div>${s.name} <span style="opacity:0.6">(${s.type})</span> — ${s.room||"no room"}</div>`)}
                  </div>
                </div>
              </div>
            `:""}
        ${t.changed.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--warning-color,#ff9800)">~</span>
                <div>
                  <div class="diag-label">Changed (${t.changed.length})</div>
                  <div class="diag-detail">
                    ${t.changed.map(s=>a`<div>${s.old.name} → ${s.new.name} <span style="opacity:0.6">(${s.new.type})</span></div>`)}
                  </div>
                </div>
              </div>
            `:""}
      </div>
    `}};A.styles=_`
    :host {
      display: block;
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
  `,l([m({attribute:!1})],A.prototype,"hass",2),l([m({type:Number})],A.prototype,"refreshKey",2),l([m({type:String})],A.prototype,"miniserverId",2),l([p()],A.prototype,"_status",2),l([p()],A.prototype,"_diff",2),l([p()],A.prototype,"_loading",2),l([p()],A.prototype,"_error",2),A=l([y("status-view")],A);var ot=500,C=class extends v{constructor(){super(...arguments);this._events=[];this._paused=!1;this._filter="";this._connected=!1;this._error="";this._pendingEvents=[]}connectedCallback(){super.connectedCallback(),this._subscribe()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe()}updated(t){t.has("miniserverId")&&(this._unsubscribe(),this._events=[],this._subscribe())}async _subscribe(){this._error="";try{this._unsub=await this.hass.connection.subscribeMessage(t=>{let o=t;if(o.events){if(this._paused){this._pendingEvents.push(...o.events),this._pendingEvents.length>ot&&(this._pendingEvents=this._pendingEvents.slice(-ot));return}this._events=[...o.events,...this._events].slice(0,ot)}},{type:"loxone/subscribe_events",...this.miniserverId?{miniserver:this.miniserverId}:{}}),this._connected=!0}catch(t){this._error=t instanceof Error?t.message:String(t),this._connected=!1}}_unsubscribe(){this._unsub&&(this._unsub(),this._unsub=void 0),this._connected=!1}_togglePause(){this._paused=!this._paused,!this._paused&&this._pendingEvents.length>0&&(this._events=[...this._pendingEvents,...this._events].slice(0,ot),this._pendingEvents=[])}_clear(){this._events=[],this._pendingEvents=[]}_onFilterInput(t){this._filter=t.target.value.toLowerCase()}_formatTime(t){try{return new Date(t).toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:1})}catch{return t}}_formatValue(t){return t==null?"\u2014":typeof t=="number"?Number.isInteger(t)?String(t):t.toFixed(2):typeof t=="object"?JSON.stringify(t):String(t)}render(){let t=this._filter,o=t?this._events.filter(r=>r.name.toLowerCase().includes(t)||r.room.toLowerCase().includes(t)||r.uuid.toLowerCase().includes(t)):this._events;return a`
      <div class="toolbar">
        <span class="status-dot ${this._connected?"on":"off"}"></span>
        <button class="${this._paused?"active":""}" @click=${this._togglePause}>
          ${this._paused?"\u25B6 Resume":"\u23F8 Pause"}
        </button>
        <button @click=${this._clear}>Clear</button>
        <input
          type="text"
          placeholder="Filter by name, room, UUID…"
          .value=${this._filter}
          @input=${this._onFilterInput}
        />
        <span class="count">${o.length} event${o.length!==1?"s":""}</span>
        ${this._error?a`<span class="error">${this._error}</span>`:""}
      </div>
      <div class="log-container">
        ${o.length===0?a`<div class="empty">
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
                    ${o.map(r=>a`
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
    `}};C.styles=_`
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
  `,l([m({attribute:!1})],C.prototype,"hass",2),l([m({type:String})],C.prototype,"miniserverId",2),l([p()],C.prototype,"_events",2),l([p()],C.prototype,"_paused",2),l([p()],C.prototype,"_filter",2),l([p()],C.prototype,"_connected",2),l([p()],C.prototype,"_error",2),C=l([y("monitor-view")],C);var qt="loxone_console_history",ft=50,w=class extends v{constructor(){super(...arguments);this._uuid="";this._command="";this._sending=!1;this._history=[];this._devices=[];this._suggestions=[];this._selectedDevice=null}connectedCallback(){super.connectedCallback(),this._loadHistory(),this._loadDevices()}updated(t){t.has("miniserverId")&&this._loadDevices()}_loadHistory(){try{let t=localStorage.getItem(qt);t&&(this._history=JSON.parse(t))}catch{}}_saveHistory(){try{localStorage.setItem(qt,JSON.stringify(this._history.slice(-ft)))}catch{}}async _loadDevices(){try{let t=await U(this.hass,this.miniserverId);this._devices=t.devices}catch{}}_onUuidInput(t){this._uuid=t.target.value,this._selectedDevice=null;let o=this._uuid.toLowerCase();o.length>=2?this._suggestions=this._devices.filter(r=>r.name.toLowerCase().includes(o)||r.uuid.toLowerCase().includes(o)||r.type.toLowerCase().includes(o)).slice(0,8):this._suggestions=[]}_selectSuggestion(t){this._uuid=t.uuid,this._selectedDevice=t,this._suggestions=[]}_getCommandHints(){if(!this._selectedDevice)return[];switch(this._selectedDevice.type){case"Switch":return["On","Off","pulse"];case"Dimmer":case"EIBDimmer":return["On","Off","0","50","100"];case"Slider":return["0","50","100"];case"Jalousie":return["up","down","fullUp","fullDown","shade","stop"];case"Gate":return["open","close","stop"];case"LightController":case"LightControllerV2":return["on","off","plus","minus","changeTo/1"];case"IRoomController":case"IRoomControllerV2":return["setComfortTemperature/21","setEcoOffset/2","operatingMode/0"];case"Alarm":return["on","off","delayedOn"];case"ColorPickerV2":return["hsv(0,100,100)","temp(2700,100)"];case"TextInput":return[];default:return["On","Off","pulse"]}}_applyHint(t){this._command=t}_onCommandInput(t){this._command=t.target.value}_onKeyDown(t){t.key==="Enter"&&this._uuid&&this._command&&this._send(),t.key==="Escape"&&(this._suggestions=[])}async _send(){if(!this._uuid||!this._command||this._sending)return;this._sending=!0,this._suggestions=[];let t=new Date().toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),o=this._selectedDevice?.name,r=this._selectedDevice?.uuid||this._uuid;try{let s=await jt(this.hass,r,this._command,this.miniserverId);S(this,`Sent "${this._command}" to ${o||r}`),this._history=[...this._history,{uuid:r,name:o,command:this._command,result:"OK",ok:!0,timestamp:t}].slice(-ft)}catch(s){let n=s instanceof Error?s.message:String(s);S(this,`Error: ${n}`),this._history=[...this._history,{uuid:r,name:o,command:this._command,result:n,ok:!1,timestamp:t}].slice(-ft)}finally{this._sending=!1,this._saveHistory()}}_clearHistory(){this._history=[],this._saveHistory()}render(){return a`
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
                    ${this._suggestions.map(t=>a`
                        <div class="suggestion" @mousedown=${()=>this._selectSuggestion(t)}>
                          <span class="name">${t.name}</span>
                          <span class="type">${t.type}</span>
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
                  ${this._getCommandHints().map(t=>a`<button class="command-chip" @click=${()=>this._applyHint(t)}>${t}</button>`)}
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
                  ${[...this._history].reverse().map(t=>a`
                      <tr>
                        <td>${t.timestamp}</td>
                        <td>${t.name?a`${t.name} <span class="sel-uuid">${t.uuid}</span>`:t.uuid}</td>
                        <td>${t.command}</td>
                        <td class="${t.ok?"result-ok":"result-err"}">${t.result}</td>
                      </tr>
                    `)}
                </tbody>
              </table>
            `}
      </div>
    `}};w.styles=_`
    :host {
      display: block;
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
  `,l([m({attribute:!1})],w.prototype,"hass",2),l([m({type:String})],w.prototype,"miniserverId",2),l([p()],w.prototype,"_uuid",2),l([p()],w.prototype,"_command",2),l([p()],w.prototype,"_sending",2),l([p()],w.prototype,"_history",2),l([p()],w.prototype,"_devices",2),l([p()],w.prototype,"_suggestions",2),l([p()],w.prototype,"_selectedDevice",2),w=l([y("console-view")],w);var rt=500,me={DEBUG:"var(--secondary-text-color, #727272)",INFO:"var(--primary-color, #03a9f4)",WARNING:"var(--warning-color, #ff9800)",ERROR:"var(--error-color, #db4437)",CRITICAL:"var(--error-color, #db4437)"},Jt={DEBUG:10,INFO:20,WARNING:30,ERROR:40,CRITICAL:50},R=class extends v{constructor(){super(...arguments);this._logs=[];this._paused=!1;this._filter="";this._levelFilter="";this._connected=!1;this._error="";this._pending=[]}connectedCallback(){super.connectedCallback(),this._subscribe()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe()}async _subscribe(){this._error="";try{this._unsub=await this.hass.connection.subscribeMessage(t=>{let o=t;if(!o.message)return;let r={name:o.name,level:o.level,message:o.message,timestamp:o.timestamp};if(this._paused){this._pending.push(r),this._pending.length>rt&&(this._pending=this._pending.slice(-rt));return}this._logs=[r,...this._logs].slice(0,rt)},{type:"loxone/subscribe_logs"}),this._connected=!0}catch(t){this._error=t instanceof Error?t.message:String(t),this._connected=!1}}_unsubscribe(){this._unsub&&(this._unsub(),this._unsub=void 0),this._connected=!1}_togglePause(){this._paused=!this._paused,!this._paused&&this._pending.length>0&&(this._logs=[...this._pending.reverse(),...this._logs].slice(0,rt),this._pending=[])}_clear(){this._logs=[],this._pending=[]}_formatTime(t){try{return new Date(t*1e3).toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}catch{return String(t)}}_shortName(t){return t.replace(/^custom_components\.loxone\.?/,"")}render(){let t=this._filter.toLowerCase(),o=this._levelFilter,r=this._logs;if(t&&(r=r.filter(s=>s.message.toLowerCase().includes(t)||s.name.toLowerCase().includes(t))),o){let s=Jt[o]??0;r=r.filter(n=>(Jt[n.level]??0)>=s)}return a`
      <div class="toolbar">
        <span class="status-dot ${this._connected?"on":"off"}"></span>
        <button class="${this._paused?"active":""}" @click=${this._togglePause}>
          ${this._paused?"\u25B6 Resume":"\u23F8 Pause"}
        </button>
        <button @click=${this._clear}>Clear</button>
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
                  <span class="log-level" style="color:${me[s.level]||"inherit"}">${s.level}</span>
                  <span class="log-name" title=${s.name}>${this._shortName(s.name)}</span>
                  <span class="log-msg">${s.message}</span>
                </div>
              `)}
            </div>
          `}
      </div>
    `}};R.styles=_`
    :host { display: block; }
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
  `,l([m({attribute:!1})],R.prototype,"hass",2),l([p()],R.prototype,"_logs",2),l([p()],R.prototype,"_paused",2),l([p()],R.prototype,"_filter",2),l([p()],R.prototype,"_levelFilter",2),l([p()],R.prototype,"_connected",2),l([p()],R.prototype,"_error",2),R=l([y("logs-view")],R);var E=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._data=null;this._loading=!0;this._error="";this._filter="";this._groupBy="room";this._expanded=new Set}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{this._data=await Wt(this.hass,this.miniserverId)}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}_toggle(t){let o=new Set(this._expanded);o.has(t)?o.delete(t):o.add(t),this._expanded=o}_groupControls(t){let o=new Map;for(let r of t){let s=this._groupBy==="room"?r.room||"No room":this._groupBy==="category"?r.category||"No category":r.type,n=o.get(s)||[];n.push(r),o.set(s,n)}return new Map([...o.entries()].sort((r,s)=>r[0].localeCompare(s[0])))}render(){if(this._loading)return a`<p class="status">Loading structure…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;if(!this._data)return a`<p class="status">No data.</p>`;let t=this._data.controls;if(this._filter){let s=this._filter.toLowerCase();t=t.filter(n=>n.name.toLowerCase().includes(s)||n.type.toLowerCase().includes(s)||n.room.toLowerCase().includes(s)||n.uuid.toLowerCase().includes(s))}let o=this._groupControls(t),r=t.reduce((s,n)=>s+n.sub_controls.length,0);return a`
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
        <span class="count">${t.length}</span> controls,
        <span class="count">${r}</span> sub-controls,
        <span class="count">${this._data.rooms.length}</span> rooms,
        <span class="count">${this._data.categories.length}</span> categories
      </p>
      ${[...o.entries()].map(([s,n])=>{let d=`g_${s}`,c=this._expanded.has(d);return a`
          <div class="group-card">
            <div class="group-header" @click=${()=>this._toggle(d)}>
              <div><span class="arrow">${c?"\u25BC":"\u25B6"}</span>${s}</div>
              <span class="group-count">${n.length}</span>
            </div>
            ${c?n.map(h=>a`
              <div class="ctrl-row">
                <div>
                  <span class="ctrl-name">${h.name}</span>
                  ${h.states.length>0?a`
                    <div class="states-chips">
                      ${h.states.map(u=>a`<span class="state-chip">${u}</span>`)}
                    </div>
                  `:f}
                </div>
                <div class="ctrl-meta">
                  <span class="badge">${h.type}</span>
                  <span style="font-family:var(--ha-font-family-code,monospace);font-size:10px;opacity:0.6"
                        title=${h.uuid}>${h.uuid.slice(0,8)}…</span>
                </div>
              </div>
              ${h.sub_controls.map(u=>a`
                <div class="sub-row">
                  ${u.name} <span class="badge">${u.type}</span>
                  ${u.states.length>0?a`
                    <div class="states-chips">
                      ${u.states.map(g=>a`<span class="state-chip">${g}</span>`)}
                    </div>
                  `:f}
                </div>
              `)}
            `):f}
          </div>
        `})}
    `}};E.styles=_`
    :host { display: block; }
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
  `,l([m({attribute:!1})],E.prototype,"hass",2),l([m({type:Number})],E.prototype,"refreshKey",2),l([m({type:String})],E.prototype,"miniserverId",2),l([p()],E.prototype,"_data",2),l([p()],E.prototype,"_loading",2),l([p()],E.prototype,"_error",2),l([p()],E.prototype,"_filter",2),l([p()],E.prototype,"_groupBy",2),l([p()],E.prototype,"_expanded",2),E=l([y("structure-view")],E);var Yt=["devices","areas","bridges","monitor","console","logs","structure","status"];function Xt(){let i=window.location.hash.replace(/^#/,"").split("?")[0];return Yt.includes(i)?i:"devices"}var D=class extends v{constructor(){super(...arguments);this._activeTab=Xt();this._refreshKey=0;this._entries=[];this._onHashChange=()=>{this._activeTab=Xt()}}connectedCallback(){super.connectedCallback(),window.addEventListener("hashchange",this._onHashChange),this._loadEntries()}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("hashchange",this._onHashChange)}async _loadEntries(){try{let t=await Tt(this.hass);this._entries=t.entries,!this._selectedMiniserver&&this._entries.length>0&&(this._selectedMiniserver=this._entries[0].miniserver)}catch{}}_setTab(t){this._activeTab=t,window.location.hash=t==="devices"?"":t}_refresh(){this._refreshKey++}_onEntryChange(t){let o=t.target;this._selectedMiniserver=o.value,this._refreshKey++}render(){let t=this._entries.length>1;return a`
      <div class="header">
        <div class="header-left">
          <h1>Loxone</h1>
          ${t?a`
                <select
                  class="entry-select"
                  .value=${this._selectedMiniserver??""}
                  @change=${this._onEntryChange}
                >
                  ${this._entries.map(o=>a`
                      <option value=${o.miniserver}>
                        ${o.name||o.title||o.host}
                      </option>
                    `)}
                </select>
              `:f}
        </div>
        <button class="refresh-btn" @click=${this._refresh}>↻ Refresh</button>
      </div>
      <div class="tabs">
        ${Yt.map(o=>a`
            <div
              class="tab ${this._activeTab===o?"active":""}"
              @click=${()=>this._setTab(o)}
            >
              ${o.charAt(0).toUpperCase()+o.slice(1)}
            </div>
          `)}
      </div>
      ${this._renderTab()}
    `}_renderTab(){let t=this._refreshKey,o=this._selectedMiniserver;switch(this._activeTab){case"devices":return a`<devices-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${o}></devices-view>`;case"areas":return a`<areas-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${o}></areas-view>`;case"bridges":return a`<bridges-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${o}></bridges-view>`;case"monitor":return a`<monitor-view .hass=${this.hass} .miniserverId=${o}></monitor-view>`;case"console":return a`<console-view .hass=${this.hass} .miniserverId=${o}></console-view>`;case"logs":return a`<logs-view .hass=${this.hass}></logs-view>`;case"structure":return a`<structure-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${o}></structure-view>`;case"status":return a`<status-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${o}></status-view>`}}};D.styles=_`
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
    .tabs {
      display: flex;
      gap: 0;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--divider-color, #e0e0e0);
      overflow-x: auto;
    }
    .tab {
      padding: 10px 20px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      color: var(--secondary-text-color, #727272);
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      transition: color 0.2s, border-color 0.2s;
      user-select: none;
      white-space: nowrap;
    }
    .tab:hover {
      color: var(--primary-text-color, #212121);
    }
    .tab.active {
      color: var(--primary-color, #03a9f4);
      border-bottom-color: var(--primary-color, #03a9f4);
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
