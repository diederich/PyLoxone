var Dt=Object.defineProperty;var Mt=Object.getOwnPropertyDescriptor;var d=(r,e,t,s)=>{for(var o=s>1?void 0:s?Mt(e,t):e,n=r.length-1,i;n>=0;n--)(i=r[n])&&(o=(s?i(e,t,o):i(o))||o);return s&&o&&Dt(e,t,o),o};var F=globalThis,q=F.ShadowRoot&&(F.ShadyCSS===void 0||F.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,X=Symbol(),ct=new WeakMap,M=class{constructor(e,t,s){if(this._$cssResult$=!0,s!==X)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(q&&e===void 0){let s=t!==void 0&&t.length===1;s&&(e=ct.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),s&&ct.set(t,e))}return e}toString(){return this.cssText}},dt=r=>new M(typeof r=="string"?r:r+"",void 0,X),x=(r,...e)=>{let t=r.length===1?r[0]:e.reduce((s,o,n)=>s+(i=>{if(i._$cssResult$===!0)return i.cssText;if(typeof i=="number")return i;throw Error("Value passed to 'css' function must be a 'css' function result: "+i+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(o)+r[n+1],r[0]);return new M(t,r,X)},pt=(r,e)=>{if(q)r.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let s=document.createElement("style"),o=F.litNonce;o!==void 0&&s.setAttribute("nonce",o),s.textContent=t.cssText,r.appendChild(s)}},Y=q?r=>r:r=>r instanceof CSSStyleSheet?(e=>{let t="";for(let s of e.cssRules)t+=s.cssText;return dt(t)})(r):r;var{is:zt,defineProperty:Ut,getOwnPropertyDescriptor:Nt,getOwnPropertyNames:Ot,getOwnPropertySymbols:Kt,getPrototypeOf:It}=Object,G=globalThis,ht=G.trustedTypes,Bt=ht?ht.emptyScript:"",jt=G.reactiveElementPolyfillSupport,z=(r,e)=>r,U={toAttribute(r,e){switch(e){case Boolean:r=r?Bt:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,e){let t=r;switch(e){case Boolean:t=r!==null;break;case Number:t=r===null?null:Number(r);break;case Object:case Array:try{t=JSON.parse(r)}catch{t=null}}return t}},W=(r,e)=>!zt(r,e),ut={attribute:!0,type:String,converter:U,reflect:!1,useDefault:!1,hasChanged:W};Symbol.metadata??=Symbol("metadata"),G.litPropertyMetadata??=new WeakMap;var E=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=ut){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let s=Symbol(),o=this.getPropertyDescriptor(e,s,t);o!==void 0&&Ut(this.prototype,e,o)}}static getPropertyDescriptor(e,t,s){let{get:o,set:n}=Nt(this.prototype,e)??{get(){return this[t]},set(i){this[t]=i}};return{get:o,set(i){let a=o?.call(this);n?.call(this,i),this.requestUpdate(e,a,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??ut}static _$Ei(){if(this.hasOwnProperty(z("elementProperties")))return;let e=It(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(z("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(z("properties"))){let t=this.properties,s=[...Ot(t),...Kt(t)];for(let o of s)this.createProperty(o,t[o])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[s,o]of t)this.elementProperties.set(s,o)}this._$Eh=new Map;for(let[t,s]of this.elementProperties){let o=this._$Eu(t,s);o!==void 0&&this._$Eh.set(o,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let s=new Set(e.flat(1/0).reverse());for(let o of s)t.unshift(Y(o))}else e!==void 0&&t.push(Y(e));return t}static _$Eu(e,t){let s=t.attribute;return s===!1?void 0:typeof s=="string"?s:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let s of t.keys())this.hasOwnProperty(s)&&(e.set(s,this[s]),delete this[s]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return pt(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,s){this._$AK(e,s)}_$ET(e,t){let s=this.constructor.elementProperties.get(e),o=this.constructor._$Eu(e,s);if(o!==void 0&&s.reflect===!0){let n=(s.converter?.toAttribute!==void 0?s.converter:U).toAttribute(t,s.type);this._$Em=e,n==null?this.removeAttribute(o):this.setAttribute(o,n),this._$Em=null}}_$AK(e,t){let s=this.constructor,o=s._$Eh.get(e);if(o!==void 0&&this._$Em!==o){let n=s.getPropertyOptions(o),i=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:U;this._$Em=o;let a=i.fromAttribute(t,n.type);this[o]=a??this._$Ej?.get(o)??a,this._$Em=null}}requestUpdate(e,t,s,o=!1,n){if(e!==void 0){let i=this.constructor;if(o===!1&&(n=this[e]),s??=i.getPropertyOptions(e),!((s.hasChanged??W)(n,t)||s.useDefault&&s.reflect&&n===this._$Ej?.get(e)&&!this.hasAttribute(i._$Eu(e,s))))return;this.C(e,t,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:s,reflect:o,wrapped:n},i){s&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,i??t??this[e]),n!==!0||i!==void 0)||(this._$AL.has(e)||(this.hasUpdated||s||(t=void 0),this._$AL.set(e,t)),o===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[o,n]of this._$Ep)this[o]=n;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[o,n]of s){let{wrapped:i}=n,a=this[o];i!==!0||this._$AL.has(o)||a===void 0||this.C(o,void 0,n,a)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(t)):this._$EM()}catch(s){throw e=!1,this._$EM(),s}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};E.elementStyles=[],E.shadowRootOptions={mode:"open"},E[z("elementProperties")]=new Map,E[z("finalized")]=new Map,jt?.({ReactiveElement:E}),(G.reactiveElementVersions??=[]).push("2.1.2");var it=globalThis,ft=r=>r,J=it.trustedTypes,mt=J?J.createPolicy("lit-html",{createHTML:r=>r}):void 0,xt="$lit$",k=`lit$${Math.random().toFixed(9).slice(2)}$`,$t="?"+k,Ft=`<${$t}>`,R=document,O=()=>R.createComment(""),K=r=>r===null||typeof r!="object"&&typeof r!="function",nt=Array.isArray,qt=r=>nt(r)||typeof r?.[Symbol.iterator]=="function",V=`[ 	
\f\r]`,N=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,gt=/-->/g,vt=/>/g,L=RegExp(`>|${V}(?:([^\\s"'>=/]+)(${V}*=${V}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),_t=/'/g,yt=/"/g,wt=/^(?:script|style|textarea|title)$/i,at=r=>(e,...t)=>({_$litType$:r,strings:e,values:t}),c=at(1),oe=at(2),re=at(3),P=Symbol.for("lit-noChange"),f=Symbol.for("lit-nothing"),bt=new WeakMap,H=R.createTreeWalker(R,129);function At(r,e){if(!nt(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return mt!==void 0?mt.createHTML(e):e}var Gt=(r,e)=>{let t=r.length-1,s=[],o,n=e===2?"<svg>":e===3?"<math>":"",i=N;for(let a=0;a<t;a++){let l=r[a],h,g,u=-1,A=0;for(;A<l.length&&(i.lastIndex=A,g=i.exec(l),g!==null);)A=i.lastIndex,i===N?g[1]==="!--"?i=gt:g[1]!==void 0?i=vt:g[2]!==void 0?(wt.test(g[2])&&(o=RegExp("</"+g[2],"g")),i=L):g[3]!==void 0&&(i=L):i===L?g[0]===">"?(i=o??N,u=-1):g[1]===void 0?u=-2:(u=i.lastIndex-g[2].length,h=g[1],i=g[3]===void 0?L:g[3]==='"'?yt:_t):i===yt||i===_t?i=L:i===gt||i===vt?i=N:(i=L,o=void 0);let S=i===L&&r[a+1].startsWith("/>")?" ":"";n+=i===N?l+Ft:u>=0?(s.push(h),l.slice(0,u)+xt+l.slice(u)+k+S):l+k+(u===-2?a:S)}return[At(r,n+(r[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),s]},I=class r{constructor({strings:e,_$litType$:t},s){let o;this.parts=[];let n=0,i=0,a=e.length-1,l=this.parts,[h,g]=Gt(e,t);if(this.el=r.createElement(h,s),H.currentNode=this.el.content,t===2||t===3){let u=this.el.content.firstChild;u.replaceWith(...u.childNodes)}for(;(o=H.nextNode())!==null&&l.length<a;){if(o.nodeType===1){if(o.hasAttributes())for(let u of o.getAttributeNames())if(u.endsWith(xt)){let A=g[i++],S=o.getAttribute(u).split(k),j=/([.?@])?(.*)/.exec(A);l.push({type:1,index:n,name:j[2],strings:S,ctor:j[1]==="."?et:j[1]==="?"?st:j[1]==="@"?ot:D}),o.removeAttribute(u)}else u.startsWith(k)&&(l.push({type:6,index:n}),o.removeAttribute(u));if(wt.test(o.tagName)){let u=o.textContent.split(k),A=u.length-1;if(A>0){o.textContent=J?J.emptyScript:"";for(let S=0;S<A;S++)o.append(u[S],O()),H.nextNode(),l.push({type:2,index:++n});o.append(u[A],O())}}}else if(o.nodeType===8)if(o.data===$t)l.push({type:2,index:n});else{let u=-1;for(;(u=o.data.indexOf(k,u+1))!==-1;)l.push({type:7,index:n}),u+=k.length-1}n++}}static createElement(e,t){let s=R.createElement("template");return s.innerHTML=e,s}};function T(r,e,t=r,s){if(e===P)return e;let o=s!==void 0?t._$Co?.[s]:t._$Cl,n=K(e)?void 0:e._$litDirective$;return o?.constructor!==n&&(o?._$AO?.(!1),n===void 0?o=void 0:(o=new n(r),o._$AT(r,t,s)),s!==void 0?(t._$Co??=[])[s]=o:t._$Cl=o),o!==void 0&&(e=T(r,o._$AS(r,e.values),o,s)),e}var tt=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:s}=this._$AD,o=(e?.creationScope??R).importNode(t,!0);H.currentNode=o;let n=H.nextNode(),i=0,a=0,l=s[0];for(;l!==void 0;){if(i===l.index){let h;l.type===2?h=new B(n,n.nextSibling,this,e):l.type===1?h=new l.ctor(n,l.name,l.strings,this,e):l.type===6&&(h=new rt(n,this,e)),this._$AV.push(h),l=s[++a]}i!==l?.index&&(n=H.nextNode(),i++)}return H.currentNode=R,o}p(e){let t=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(e,s,t),t+=s.strings.length-2):s._$AI(e[t])),t++}},B=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,s,o){this.type=2,this._$AH=f,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=s,this.options=o,this._$Cv=o?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=T(this,e,t),K(e)?e===f||e==null||e===""?(this._$AH!==f&&this._$AR(),this._$AH=f):e!==this._$AH&&e!==P&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):qt(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==f&&K(this._$AH)?this._$AA.nextSibling.data=e:this.T(R.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:s}=e,o=typeof s=="number"?this._$AC(e):(s.el===void 0&&(s.el=I.createElement(At(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===o)this._$AH.p(t);else{let n=new tt(o,this),i=n.u(this.options);n.p(t),this.T(i),this._$AH=n}}_$AC(e){let t=bt.get(e.strings);return t===void 0&&bt.set(e.strings,t=new I(e)),t}k(e){nt(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,s,o=0;for(let n of e)o===t.length?t.push(s=new r(this.O(O()),this.O(O()),this,this.options)):s=t[o],s._$AI(n),o++;o<t.length&&(this._$AR(s&&s._$AB.nextSibling,o),t.length=o)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let s=ft(e).nextSibling;ft(e).remove(),e=s}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},D=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,s,o,n){this.type=1,this._$AH=f,this._$AN=void 0,this.element=e,this.name=t,this._$AM=o,this.options=n,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=f}_$AI(e,t=this,s,o){let n=this.strings,i=!1;if(n===void 0)e=T(this,e,t,0),i=!K(e)||e!==this._$AH&&e!==P,i&&(this._$AH=e);else{let a=e,l,h;for(e=n[0],l=0;l<n.length-1;l++)h=T(this,a[s+l],t,l),h===P&&(h=this._$AH[l]),i||=!K(h)||h!==this._$AH[l],h===f?e=f:e!==f&&(e+=(h??"")+n[l+1]),this._$AH[l]=h}i&&!o&&this.j(e)}j(e){e===f?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},et=class extends D{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===f?void 0:e}},st=class extends D{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==f)}},ot=class extends D{constructor(e,t,s,o,n){super(e,t,s,o,n),this.type=5}_$AI(e,t=this){if((e=T(this,e,t,0)??f)===P)return;let s=this._$AH,o=e===f&&s!==f||e.capture!==s.capture||e.once!==s.once||e.passive!==s.passive,n=e!==f&&(s===f||o);o&&this.element.removeEventListener(this.name,this,s),n&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},rt=class{constructor(e,t,s){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(e){T(this,e)}};var Wt=it.litHtmlPolyfillSupport;Wt?.(I,B),(it.litHtmlVersions??=[]).push("3.3.2");var Et=(r,e,t)=>{let s=t?.renderBefore??e,o=s._$litPart$;if(o===void 0){let n=t?.renderBefore??null;s._$litPart$=o=new B(e.insertBefore(O(),n),n,void 0,t??{})}return o._$AI(r),o};var lt=globalThis,v=class extends E{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=Et(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return P}};v._$litElement$=!0,v.finalized=!0,lt.litElementHydrateSupport?.({LitElement:v});var Jt=lt.litElementPolyfillSupport;Jt?.({LitElement:v});(lt.litElementVersions??=[]).push("4.2.2");var $=r=>(e,t)=>{t!==void 0?t.addInitializer(()=>{customElements.define(r,e)}):customElements.define(r,e)};var Zt={attribute:!0,type:String,converter:U,reflect:!1,hasChanged:W},Qt=(r=Zt,e,t)=>{let{kind:s,metadata:o}=t,n=globalThis.litPropertyMetadata.get(o);if(n===void 0&&globalThis.litPropertyMetadata.set(o,n=new Map),s==="setter"&&((r=Object.create(r)).wrapped=!0),n.set(t.name,r),s==="accessor"){let{name:i}=t;return{set(a){let l=e.get.call(this);e.set.call(this,a),this.requestUpdate(i,l,r,!0,a)},init(a){return a!==void 0&&this.C(i,void 0,r,a),a}}}if(s==="setter"){let{name:i}=t;return function(a){let l=this[i];e.call(this,a),this.requestUpdate(i,l,r,!0,a)}}throw Error("Unsupported decorator location: "+s)};function _(r){return(e,t)=>typeof t=="object"?Qt(r,e,t):((s,o,n)=>{let i=o.hasOwnProperty(n);return o.constructor.createProperty(n,s),i?Object.getOwnPropertyDescriptor(o,n):void 0})(r,e,t)}function p(r){return _({...r,state:!0,attribute:!1})}async function Q(r){return r.callWS({type:"loxone/get_devices"})}async function St(r,e,t){return r.callWS({type:"loxone/set_entity_enabled",entity_id:e,enabled:t})}async function kt(r){return r.callWS({type:"loxone/get_areas"})}async function Ct(r,e){await r.callService("loxone","sync_areas",{create_areas:e})}async function Lt(r){await r.callService("loxone","sync_device_names")}async function Ht(r){return r.callWS({type:"loxone/get_bridges"})}async function Rt(r,e,t){return r.callWS({type:"loxone/add_bridge",entity_id:e,loxone_uuid:t})}async function Pt(r,e){return r.callWS({type:"loxone/remove_bridge",entity_id:e})}async function Tt(r){return r.callWS({type:"loxone/get_status"})}var y=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._devices=[];this._filter="";this._loading=!0;this._error="";this._sortKey="room";this._sortDir="asc"}connectedCallback(){super.connectedCallback(),this._loadDevices()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._loadDevices()}async _loadDevices(){this._loading=!0,this._error="";try{let t=await Q(this.hass);this._devices=t.devices}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}get _filteredDevices(){let t=this._devices;if(this._filter){let s=this._filter.toLowerCase();t=t.filter(o=>o.name.toLowerCase().includes(s)||o.type.toLowerCase().includes(s)||o.room.toLowerCase().includes(s)||o.ha_entities.some(n=>n.entity_id.toLowerCase().includes(s)))}return this._sortDevices(t)}_sortDevices(t){let s=[...t],o=this._sortDir==="asc"?1:-1;return s.sort((n,i)=>{let a=0;switch(this._sortKey){case"name":a=n.name.localeCompare(i.name);break;case"type":a=n.type.localeCompare(i.type)||n.name.localeCompare(i.name);break;case"room":a=(n.room||"").localeCompare(i.room||"")||n.name.localeCompare(i.name);break;case"entities":a=n.ha_entities.length-i.ha_entities.length;break}return a*o}),s}_toggleSort(t){this._sortKey===t?this._sortDir=this._sortDir==="asc"?"desc":"asc":(this._sortKey=t,this._sortDir="asc")}_sortIndicator(t){return this._sortKey!==t?f:c`<span class="sort-arrow"
      >${this._sortDir==="asc"?"\u25B2":"\u25BC"}</span
    >`}async _toggleEntity(t,s){try{await St(this.hass,t,s),await this._loadDevices()}catch(o){this._error=o instanceof Error?o.message:String(o)}}render(){if(this._loading)return c`<p class="status">Loading devices…</p>`;if(this._error)return c`<p class="status error">Error: ${this._error}</p>`;let t=this._filteredDevices,s=new Map;for(let i of this._devices)for(let a of i.ha_entities){let l=a.entity_id.split(".")[0];s.set(l,(s.get(l)||0)+1)}let o=[...s.values()].reduce((i,a)=>i+a,0),n=[...s.entries()].sort((i,a)=>a[1]-i[1]).map(([i,a])=>`${a} ${i}`).join(", ");return c`
      <div class="toolbar">
        <input
          type="search"
          placeholder="Filter by name, type, room, or entity…"
          .value=${this._filter}
          @input=${i=>{this._filter=i.target.value}}
        />
        
      </div>
      <p class="summary">
        <span class="count">${this._devices.length}</span> controls,
        <span class="count">${o}</span> HA entities
        ${n?c`<span class="domain-breakdown">(${n})</span>`:""}
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
          ${t.map(i=>c`
              <tr class=${i.parent?"sub-control":""}>
                <td>${i.name}</td>
                <td><span class="badge">${i.type}</span></td>
                <td>${i.room||"\u2014"}</td>
                <td>
                  ${i.ha_entities.length===0?c`<span style="color: var(--secondary-text-color)"
                        >—</span
                      >`:i.ha_entities.map(a=>c`
                          <span
                            class="entity-chip ${a.disabled_by?"disabled":""}"
                          >
                            ${a.entity_id}
                            <button
                              class="toggle-btn"
                              title=${a.disabled_by?"Enable":"Disable"}
                              @click=${()=>this._toggleEntity(a.entity_id,!!a.disabled_by)}
                            >
                              ${a.disabled_by?"\u2B1A":"\u2713"}
                            </button>
                          </span>
                        `)}
                </td>
              </tr>
            `)}
        </tbody>
      </table>
    `}};y.styles=x`
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
  `,d([_({attribute:!1})],y.prototype,"hass",2),d([_({type:Number})],y.prototype,"refreshKey",2),d([p()],y.prototype,"_devices",2),d([p()],y.prototype,"_filter",2),d([p()],y.prototype,"_loading",2),d([p()],y.prototype,"_error",2),d([p()],y.prototype,"_sortKey",2),d([p()],y.prototype,"_sortDir",2),y=d([$("devices-view")],y);var b=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._rooms=[];this._haAreas=[];this._loading=!0;this._syncing=!1;this._error="";this._message=""}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let t=await kt(this.hass);this._rooms=t.rooms,this._haAreas=t.ha_areas}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}async _syncAreas(t){this._syncing=!0,this._message="",this._error="";try{await Lt(this.hass),await Ct(this.hass,t),this._message=t?"Synced areas and created missing ones.":"Synced devices to existing areas.",await this._load()}catch(s){this._error=s instanceof Error?s.message:String(s)}finally{this._syncing=!1}}render(){if(this._loading)return c`<p class="status">Loading areas…</p>`;if(this._error)return c`<p class="status error">Error: ${this._error}</p>`;let t=this._rooms.filter(o=>o.ha_area_id).length,s=this._rooms.length;return c`
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
      ${this._message?c`<p class="message">${this._message}</p>`:""}
      <p class="summary">
        <span class="count">${t}</span> / ${s} Loxone rooms mapped to
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
          ${this._rooms.map(o=>c`
              <tr>
                <td>${o.name}</td>
                <td>
                  ${o.ha_area_name?c`<span class="mapped">${o.ha_area_name}</span>`:c`<span class="unmapped">Not mapped</span>`}
                </td>
                <td>${o.device_count}</td>
              </tr>
            `)}
        </tbody>
      </table>
    `}};b.styles=x`
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
  `,d([_({attribute:!1})],b.prototype,"hass",2),d([_({type:Number})],b.prototype,"refreshKey",2),d([p()],b.prototype,"_rooms",2),d([p()],b.prototype,"_haAreas",2),d([p()],b.prototype,"_loading",2),d([p()],b.prototype,"_syncing",2),d([p()],b.prototype,"_error",2),d([p()],b.prototype,"_message",2),b=d([$("areas-view")],b);var Xt=["sensor","binary_sensor","switch","light","climate","cover","fan","number","input_boolean","input_number","input_select","media_player","lock","button","select"],m=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._bridges=[];this._devices=[];this._loading=!0;this._error="";this._message="";this._newEntityId="";this._newLoxoneUuid="";this._entityFilter="";this._loxoneFilter="";this._showEntityDropdown=!1;this._showLoxoneDropdown=!1}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[t,s]=await Promise.all([Ht(this.hass),Q(this.hass)]);this._bridges=t.bridges,this._devices=s.devices}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}get _availableEntities(){let t=new Set(this._bridges.map(n=>n.entity_id)),s=new Set;for(let n of this._devices)for(let i of n.ha_entities)s.add(i.entity_id);let o=[];for(let[n,i]of Object.entries(this.hass.states)){let a=n.split(".")[0];Xt.includes(a)&&(s.has(n)||t.has(n)||o.push({entity_id:n,friendly_name:i.attributes.friendly_name||"",domain:a}))}return o.sort((n,i)=>n.domain!==i.domain?n.domain.localeCompare(i.domain):n.entity_id.localeCompare(i.entity_id)),o}get _filteredEntities(){if(!this._entityFilter)return this._availableEntities;let t=this._entityFilter.toLowerCase();return this._availableEntities.filter(s=>s.entity_id.toLowerCase().includes(t)||s.friendly_name.toLowerCase().includes(t))}_groupByKey(t,s){let o=new Map;for(let n of t){let i=s(n),a=o.get(i)||[];a.push(n),o.set(i,a)}return o}get _availableLoxoneControls(){let t=new Set(this._bridges.map(o=>o.loxone_uuid)),s=[];for(let o of this._devices)t.has(o.uuid)||s.push({uuid:o.uuid,name:o.name,type:o.type,room:o.room||"\u2014"});return s.sort((o,n)=>o.room!==n.room?o.room.localeCompare(n.room):o.name.localeCompare(n.name)),s}get _filteredLoxoneControls(){if(!this._loxoneFilter)return this._availableLoxoneControls;let t=this._loxoneFilter.toLowerCase();return this._availableLoxoneControls.filter(s=>s.name.toLowerCase().includes(t)||s.type.toLowerCase().includes(t)||s.room.toLowerCase().includes(t))}_onEntityFocus(){this._showEntityDropdown=!0}_onEntityBlur(){setTimeout(()=>{this._showEntityDropdown=!1},200)}_selectEntity(t){this._newEntityId=t,this._entityFilter=t,this._showEntityDropdown=!1}_onLoxoneFocus(){this._showLoxoneDropdown=!0}_onLoxoneBlur(){setTimeout(()=>{this._showLoxoneDropdown=!1},200)}_selectLoxone(t,s){this._newLoxoneUuid=t,this._loxoneFilter=s,this._showLoxoneDropdown=!1}async _addBridge(){if(!(!this._newEntityId||!this._newLoxoneUuid)){this._error="",this._message="";try{await Rt(this.hass,this._newEntityId,this._newLoxoneUuid),this._message=`Bridge added: ${this._newEntityId}`,this._newEntityId="",this._newLoxoneUuid="",this._entityFilter="",this._loxoneFilter="",await this._load()}catch(t){this._error=t instanceof Error?t.message:String(t)}}}async _removeBridge(t){this._error="",this._message="";try{await Pt(this.hass,t),this._message=`Bridge removed: ${t}`,await this._load()}catch(s){this._error=s instanceof Error?s.message:String(s)}}render(){if(this._loading)return c`<p class="status">Loading bridges…</p>`;if(this._error)return c`<p class="status error">Error: ${this._error}</p>`;let t=this._filteredEntities,s=this._groupByKey(t,i=>i.domain),o=this._filteredLoxoneControls,n=this._groupByKey(o,i=>i.room);return c`
      <div class="add-form">
        <div class="field">
          <label>HA Entity</label>
          <div class="combo-wrapper">
            <input
              type="text"
              placeholder="Search entities…"
              .value=${this._entityFilter}
              @input=${i=>{this._entityFilter=i.target.value,this._newEntityId=this._entityFilter,this._showEntityDropdown=!0}}
              @focus=${this._onEntityFocus}
              @blur=${this._onEntityBlur}
              autocomplete="off"
            />
            ${this._showEntityDropdown?c`
                  <div class="combo-dropdown">
                    ${t.length===0?c`<div class="combo-empty">No matching entities</div>`:Array.from(s.entries()).map(([i,a])=>c`
                            <div class="combo-group">${i}</div>
                            ${a.map(l=>c`
                                <div
                                  class="combo-option"
                                  @mousedown=${h=>{h.preventDefault(),this._selectEntity(l.entity_id)}}
                                >
                                  <span>${l.entity_id}</span>
                                  ${l.friendly_name?c`<span class="secondary"
                                        >${l.friendly_name}</span
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
              @input=${i=>{this._loxoneFilter=i.target.value,this._newLoxoneUuid="",this._showLoxoneDropdown=!0}}
              @focus=${this._onLoxoneFocus}
              @blur=${this._onLoxoneBlur}
              autocomplete="off"
            />
            ${this._showLoxoneDropdown?c`
                  <div class="combo-dropdown">
                    ${o.length===0?c`<div class="combo-empty">No matching controls</div>`:Array.from(n.entries()).map(([i,a])=>c`
                            <div class="combo-group">${i}</div>
                            ${a.map(l=>c`
                                <div
                                  class="combo-option"
                                  @mousedown=${h=>{h.preventDefault(),this._selectLoxone(l.uuid,l.name)}}
                                >
                                  <span>${l.name}</span>
                                  <span class="secondary">${l.type}</span>
                                </div>
                              `)}
                          `)}
                  </div>
                `:""}
          </div>
        </div>
        <button @click=${this._addBridge}>Add Bridge</button>
      </div>
      ${this._message?c`<p class="message">${this._message}</p>`:""}
      ${this._bridges.length===0?c`<p class="empty">No device bridges configured.</p>`:c`
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
                ${this._bridges.map(i=>{let a=this.hass.states[i.entity_id],l=a?a.state:"unavailable",h=!a||l==="unavailable"||l==="unknown"?"state-warn":"";return c`
                    <tr>
                      <td>${i.entity_id}</td>
                      <td>
                        <span class="state-value ${h}"
                          >${l}</span
                        >
                      </td>
                      <td class="direction">→</td>
                      <td>${i.loxone_name||i.loxone_uuid}</td>
                      <td><span class="badge">${i.loxone_type}</span></td>
                      <td>
                        <button
                          class="danger"
                          @click=${()=>this._removeBridge(i.entity_id)}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  `})}
              </tbody>
            </table>
          `}
    `}};m.styles=x`
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
  `,d([_({attribute:!1})],m.prototype,"hass",2),d([_({type:Number})],m.prototype,"refreshKey",2),d([p()],m.prototype,"_bridges",2),d([p()],m.prototype,"_devices",2),d([p()],m.prototype,"_loading",2),d([p()],m.prototype,"_error",2),d([p()],m.prototype,"_message",2),d([p()],m.prototype,"_newEntityId",2),d([p()],m.prototype,"_newLoxoneUuid",2),d([p()],m.prototype,"_entityFilter",2),d([p()],m.prototype,"_loxoneFilter",2),d([p()],m.prototype,"_showEntityDropdown",2),d([p()],m.prototype,"_showLoxoneDropdown",2),m=d([$("bridges-view")],m);var w=class extends v{constructor(){super(...arguments);this.refreshKey=0;this._status=null;this._loading=!0;this._error=""}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{this._status=await Tt(this.hass)}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}render(){if(this._loading)return c`<p class="status">Loading status…</p>`;if(this._error)return c`<p class="status error">Error: ${this._error}</p>`;if(!this._status)return c`<p class="status">No status available.</p>`;let t=this._status,s=t.connection_state==="connected"?"conn-connected":t.connection_state==="reconnecting"?"conn-reconnecting":"conn-disconnected",o=t.entities_without_state.length;return c`
      <div class="grid">
        <div class="card">
          <h3 class="card-title">Connection</h3>
          <div class="info-row">
            <span class="info-label">Status</span>
            <span class="conn-badge ${s}">${t.connection_state}</span>
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
          <span class="diag-icon ${o===0?"diag-ok":"diag-warn"}"
            >${o===0?"\u2713":"\u26A0"}</span
          >
          <div>
            <div class="diag-label">Entities without state</div>
            <div class="diag-detail">
              ${o===0?`All ${t.entities_enabled} enabled entities have state`:c`${o} of ${t.entities_enabled} enabled
                    entities missing state:
                    <br />
                    ${t.entities_without_state.slice(0,10).join(", ")}${o>10?` \u2026 and ${o-10} more`:""}`}
            </div>
          </div>
        </div>

        ${t.entities_disabled>0?c`
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
    `}};w.styles=x`
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
    
  `,d([_({attribute:!1})],w.prototype,"hass",2),d([_({type:Number})],w.prototype,"refreshKey",2),d([p()],w.prototype,"_status",2),d([p()],w.prototype,"_loading",2),d([p()],w.prototype,"_error",2),w=d([$("status-view")],w);var C=class extends v{constructor(){super(...arguments);this._activeTab="devices";this._refreshKey=0}_setTab(t){this._activeTab=t}_refresh(){this._refreshKey++}render(){return c`
      <div class="header">
        <h1>Loxone</h1>
        <button class="refresh-btn" @click=${this._refresh}>↻ Refresh</button>
      </div>
      <div class="tabs">
        ${["devices","areas","bridges","status"].map(t=>c`
            <div
              class="tab ${this._activeTab===t?"active":""}"
              @click=${()=>this._setTab(t)}
            >
              ${t.charAt(0).toUpperCase()+t.slice(1)}
            </div>
          `)}
      </div>
      ${this._renderTab()}
    `}_renderTab(){let t=this._refreshKey;switch(this._activeTab){case"devices":return c`<devices-view .hass=${this.hass} .refreshKey=${t}></devices-view>`;case"areas":return c`<areas-view .hass=${this.hass} .refreshKey=${t}></areas-view>`;case"bridges":return c`<bridges-view .hass=${this.hass} .refreshKey=${t}></bridges-view>`;case"status":return c`<status-view .hass=${this.hass} .refreshKey=${t}></status-view>`}}};C.styles=x`
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
    }
    h1 {
      font-size: 24px;
      font-weight: 400;
      margin: 0;
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
    }
    .tab:hover {
      color: var(--primary-text-color, #212121);
    }
    .tab.active {
      color: var(--primary-color, #03a9f4);
      border-bottom-color: var(--primary-color, #03a9f4);
    }
  `,d([_({attribute:!1})],C.prototype,"hass",2),d([p()],C.prototype,"_activeTab",2),d([p()],C.prototype,"_refreshKey",2),C=d([$("loxone-panel")],C);export{C as LoxonePanel};
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
