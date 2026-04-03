var jt=Object.defineProperty;var Bt=Object.getOwnPropertyDescriptor;var d=(r,e,t,s)=>{for(var o=s>1?void 0:s?Bt(e,t):e,i=r.length-1,n;i>=0;i--)(n=r[i])&&(o=(s?n(e,t,o):n(o))||o);return s&&o&&jt(e,t,o),o};var W=globalThis,J=W.ShadowRoot&&(W.ShadyCSS===void 0||W.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,tt=Symbol(),ut=new WeakMap,O=class{constructor(e,t,s){if(this._$cssResult$=!0,s!==tt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(J&&e===void 0){let s=t!==void 0&&t.length===1;s&&(e=ut.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),s&&ut.set(t,e))}return e}toString(){return this.cssText}},mt=r=>new O(typeof r=="string"?r:r+"",void 0,tt),y=(r,...e)=>{let t=r.length===1?r[0]:e.reduce((s,o,i)=>s+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(o)+r[i+1],r[0]);return new O(t,r,tt)},ft=(r,e)=>{if(J)r.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let s=document.createElement("style"),o=W.litNonce;o!==void 0&&s.setAttribute("nonce",o),s.textContent=t.cssText,r.appendChild(s)}},et=J?r=>r:r=>r instanceof CSSStyleSheet?(e=>{let t="";for(let s of e.cssRules)t+=s.cssText;return mt(t)})(r):r;var{is:Ft,defineProperty:qt,getOwnPropertyDescriptor:Gt,getOwnPropertyNames:Wt,getOwnPropertySymbols:Jt,getPrototypeOf:Yt}=Object,Y=globalThis,vt=Y.trustedTypes,Xt=vt?vt.emptyScript:"",Zt=Y.reactiveElementPolyfillSupport,U=(r,e)=>r,N={toAttribute(r,e){switch(e){case Boolean:r=r?Xt:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,e){let t=r;switch(e){case Boolean:t=r!==null;break;case Number:t=r===null?null:Number(r);break;case Object:case Array:try{t=JSON.parse(r)}catch{t=null}}return t}},X=(r,e)=>!Ft(r,e),gt={attribute:!0,type:String,converter:N,reflect:!1,useDefault:!1,hasChanged:X};Symbol.metadata??=Symbol("metadata"),Y.litPropertyMetadata??=new WeakMap;var C=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=gt){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let s=Symbol(),o=this.getPropertyDescriptor(e,s,t);o!==void 0&&qt(this.prototype,e,o)}}static getPropertyDescriptor(e,t,s){let{get:o,set:i}=Gt(this.prototype,e)??{get(){return this[t]},set(n){this[t]=n}};return{get:o,set(n){let c=o?.call(this);i?.call(this,n),this.requestUpdate(e,c,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??gt}static _$Ei(){if(this.hasOwnProperty(U("elementProperties")))return;let e=Yt(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(U("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(U("properties"))){let t=this.properties,s=[...Wt(t),...Jt(t)];for(let o of s)this.createProperty(o,t[o])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[s,o]of t)this.elementProperties.set(s,o)}this._$Eh=new Map;for(let[t,s]of this.elementProperties){let o=this._$Eu(t,s);o!==void 0&&this._$Eh.set(o,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let s=new Set(e.flat(1/0).reverse());for(let o of s)t.unshift(et(o))}else e!==void 0&&t.push(et(e));return t}static _$Eu(e,t){let s=t.attribute;return s===!1?void 0:typeof s=="string"?s:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let s of t.keys())this.hasOwnProperty(s)&&(e.set(s,this[s]),delete this[s]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ft(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,s){this._$AK(e,s)}_$ET(e,t){let s=this.constructor.elementProperties.get(e),o=this.constructor._$Eu(e,s);if(o!==void 0&&s.reflect===!0){let i=(s.converter?.toAttribute!==void 0?s.converter:N).toAttribute(t,s.type);this._$Em=e,i==null?this.removeAttribute(o):this.setAttribute(o,i),this._$Em=null}}_$AK(e,t){let s=this.constructor,o=s._$Eh.get(e);if(o!==void 0&&this._$Em!==o){let i=s.getPropertyOptions(o),n=typeof i.converter=="function"?{fromAttribute:i.converter}:i.converter?.fromAttribute!==void 0?i.converter:N;this._$Em=o;let c=n.fromAttribute(t,i.type);this[o]=c??this._$Ej?.get(o)??c,this._$Em=null}}requestUpdate(e,t,s,o=!1,i){if(e!==void 0){let n=this.constructor;if(o===!1&&(i=this[e]),s??=n.getPropertyOptions(e),!((s.hasChanged??X)(i,t)||s.useDefault&&s.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,s))))return;this.C(e,t,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:s,reflect:o,wrapped:i},n){s&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),i!==!0||n!==void 0)||(this._$AL.has(e)||(this.hasUpdated||s||(t=void 0),this._$AL.set(e,t)),o===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[o,i]of this._$Ep)this[o]=i;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[o,i]of s){let{wrapped:n}=i,c=this[o];n!==!0||this._$AL.has(o)||c===void 0||this.C(o,void 0,i,c)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(t)):this._$EM()}catch(s){throw e=!1,this._$EM(),s}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};C.elementStyles=[],C.shadowRootOptions={mode:"open"},C[U("elementProperties")]=new Map,C[U("finalized")]=new Map,Zt?.({ReactiveElement:C}),(Y.reactiveElementVersions??=[]).push("2.1.2");var dt=globalThis,_t=r=>r,Z=dt.trustedTypes,yt=Z?Z.createPolicy("lit-html",{createHTML:r=>r}):void 0,St="$lit$",D=`lit$${Math.random().toFixed(9).slice(2)}$`,At="?"+D,Qt=`<${At}>`,T=document,j=()=>T.createComment(""),B=r=>r===null||typeof r!="object"&&typeof r!="function",lt=Array.isArray,Vt=r=>lt(r)||typeof r?.[Symbol.iterator]=="function",st=`[ 	
\f\r]`,K=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,bt=/-->/g,xt=/>/g,H=RegExp(`>|${st}(?:([^\\s"'>=/]+)(${st}*=${st}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),$t=/'/g,wt=/"/g,kt=/^(?:script|style|textarea|title)$/i,ct=r=>(e,...t)=>({_$litType$:r,strings:e,values:t}),a=ct(1),pe=ct(2),he=ct(3),z=Symbol.for("lit-noChange"),v=Symbol.for("lit-nothing"),Et=new WeakMap,R=T.createTreeWalker(T,129);function Ct(r,e){if(!lt(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return yt!==void 0?yt.createHTML(e):e}var te=(r,e)=>{let t=r.length-1,s=[],o,i=e===2?"<svg>":e===3?"<math>":"",n=K;for(let c=0;c<t;c++){let l=r[c],p,m,u=-1,k=0;for(;k<l.length&&(n.lastIndex=k,m=n.exec(l),m!==null);)k=n.lastIndex,n===K?m[1]==="!--"?n=bt:m[1]!==void 0?n=xt:m[2]!==void 0?(kt.test(m[2])&&(o=RegExp("</"+m[2],"g")),n=H):m[3]!==void 0&&(n=H):n===H?m[0]===">"?(n=o??K,u=-1):m[1]===void 0?u=-2:(u=n.lastIndex-m[2].length,p=m[1],n=m[3]===void 0?H:m[3]==='"'?wt:$t):n===wt||n===$t?n=H:n===bt||n===xt?n=K:(n=H,o=void 0);let L=n===H&&r[c+1].startsWith("/>")?" ":"";i+=n===K?l+Qt:u>=0?(s.push(p),l.slice(0,u)+St+l.slice(u)+D+L):l+D+(u===-2?c:L)}return[Ct(r,i+(r[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),s]},F=class r{constructor({strings:e,_$litType$:t},s){let o;this.parts=[];let i=0,n=0,c=e.length-1,l=this.parts,[p,m]=te(e,t);if(this.el=r.createElement(p,s),R.currentNode=this.el.content,t===2||t===3){let u=this.el.content.firstChild;u.replaceWith(...u.childNodes)}for(;(o=R.nextNode())!==null&&l.length<c;){if(o.nodeType===1){if(o.hasAttributes())for(let u of o.getAttributeNames())if(u.endsWith(St)){let k=m[n++],L=o.getAttribute(u).split(D),G=/([.?@])?(.*)/.exec(k);l.push({type:1,index:i,name:G[2],strings:L,ctor:G[1]==="."?rt:G[1]==="?"?it:G[1]==="@"?nt:P}),o.removeAttribute(u)}else u.startsWith(D)&&(l.push({type:6,index:i}),o.removeAttribute(u));if(kt.test(o.tagName)){let u=o.textContent.split(D),k=u.length-1;if(k>0){o.textContent=Z?Z.emptyScript:"";for(let L=0;L<k;L++)o.append(u[L],j()),R.nextNode(),l.push({type:2,index:++i});o.append(u[k],j())}}}else if(o.nodeType===8)if(o.data===At)l.push({type:2,index:i});else{let u=-1;for(;(u=o.data.indexOf(D,u+1))!==-1;)l.push({type:7,index:i}),u+=D.length-1}i++}}static createElement(e,t){let s=T.createElement("template");return s.innerHTML=e,s}};function M(r,e,t=r,s){if(e===z)return e;let o=s!==void 0?t._$Co?.[s]:t._$Cl,i=B(e)?void 0:e._$litDirective$;return o?.constructor!==i&&(o?._$AO?.(!1),i===void 0?o=void 0:(o=new i(r),o._$AT(r,t,s)),s!==void 0?(t._$Co??=[])[s]=o:t._$Cl=o),o!==void 0&&(e=M(r,o._$AS(r,e.values),o,s)),e}var ot=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:s}=this._$AD,o=(e?.creationScope??T).importNode(t,!0);R.currentNode=o;let i=R.nextNode(),n=0,c=0,l=s[0];for(;l!==void 0;){if(n===l.index){let p;l.type===2?p=new q(i,i.nextSibling,this,e):l.type===1?p=new l.ctor(i,l.name,l.strings,this,e):l.type===6&&(p=new at(i,this,e)),this._$AV.push(p),l=s[++c]}n!==l?.index&&(i=R.nextNode(),n++)}return R.currentNode=T,o}p(e){let t=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(e,s,t),t+=s.strings.length-2):s._$AI(e[t])),t++}},q=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,s,o){this.type=2,this._$AH=v,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=s,this.options=o,this._$Cv=o?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=M(this,e,t),B(e)?e===v||e==null||e===""?(this._$AH!==v&&this._$AR(),this._$AH=v):e!==this._$AH&&e!==z&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):Vt(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==v&&B(this._$AH)?this._$AA.nextSibling.data=e:this.T(T.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:s}=e,o=typeof s=="number"?this._$AC(e):(s.el===void 0&&(s.el=F.createElement(Ct(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===o)this._$AH.p(t);else{let i=new ot(o,this),n=i.u(this.options);i.p(t),this.T(n),this._$AH=i}}_$AC(e){let t=Et.get(e.strings);return t===void 0&&Et.set(e.strings,t=new F(e)),t}k(e){lt(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,s,o=0;for(let i of e)o===t.length?t.push(s=new r(this.O(j()),this.O(j()),this,this.options)):s=t[o],s._$AI(i),o++;o<t.length&&(this._$AR(s&&s._$AB.nextSibling,o),t.length=o)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let s=_t(e).nextSibling;_t(e).remove(),e=s}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},P=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,s,o,i){this.type=1,this._$AH=v,this._$AN=void 0,this.element=e,this.name=t,this._$AM=o,this.options=i,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=v}_$AI(e,t=this,s,o){let i=this.strings,n=!1;if(i===void 0)e=M(this,e,t,0),n=!B(e)||e!==this._$AH&&e!==z,n&&(this._$AH=e);else{let c=e,l,p;for(e=i[0],l=0;l<i.length-1;l++)p=M(this,c[s+l],t,l),p===z&&(p=this._$AH[l]),n||=!B(p)||p!==this._$AH[l],p===v?e=v:e!==v&&(e+=(p??"")+i[l+1]),this._$AH[l]=p}n&&!o&&this.j(e)}j(e){e===v?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},rt=class extends P{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===v?void 0:e}},it=class extends P{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==v)}},nt=class extends P{constructor(e,t,s,o,i){super(e,t,s,o,i),this.type=5}_$AI(e,t=this){if((e=M(this,e,t,0)??v)===z)return;let s=this._$AH,o=e===v&&s!==v||e.capture!==s.capture||e.once!==s.once||e.passive!==s.passive,i=e!==v&&(s===v||o);o&&this.element.removeEventListener(this.name,this,s),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},at=class{constructor(e,t,s){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(e){M(this,e)}};var ee=dt.litHtmlPolyfillSupport;ee?.(F,q),(dt.litHtmlVersions??=[]).push("3.3.2");var Lt=(r,e,t)=>{let s=t?.renderBefore??e,o=s._$litPart$;if(o===void 0){let i=t?.renderBefore??null;s._$litPart$=o=new q(e.insertBefore(j(),i),i,void 0,t??{})}return o._$AI(r),o};var pt=globalThis,g=class extends C{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=Lt(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return z}};g._$litElement$=!0,g.finalized=!0,pt.litElementHydrateSupport?.({LitElement:g});var se=pt.litElementPolyfillSupport;se?.({LitElement:g});(pt.litElementVersions??=[]).push("4.2.2");var b=r=>(e,t)=>{t!==void 0?t.addInitializer(()=>{customElements.define(r,e)}):customElements.define(r,e)};var oe={attribute:!0,type:String,converter:N,reflect:!1,hasChanged:X},re=(r=oe,e,t)=>{let{kind:s,metadata:o}=t,i=globalThis.litPropertyMetadata.get(o);if(i===void 0&&globalThis.litPropertyMetadata.set(o,i=new Map),s==="setter"&&((r=Object.create(r)).wrapped=!0),i.set(t.name,r),s==="accessor"){let{name:n}=t;return{set(c){let l=e.get.call(this);e.set.call(this,c),this.requestUpdate(n,l,r,!0,c)},init(c){return c!==void 0&&this.C(n,void 0,r,c),c}}}if(s==="setter"){let{name:n}=t;return function(c){let l=this[n];e.call(this,c),this.requestUpdate(n,l,r,!0,c)}}throw Error("Unsupported decorator location: "+s)};function f(r){return(e,t)=>typeof t=="object"?re(r,e,t):((s,o,i)=>{let n=o.hasOwnProperty(i);return o.constructor.createProperty(i,s),n?Object.getOwnPropertyDescriptor(o,i):void 0})(r,e,t)}function h(r){return f({...r,state:!0,attribute:!1})}async function Dt(r){return r.callWS({type:"loxone/list_entries"})}async function I(r,e){return r.callWS({type:"loxone/get_devices",...e?{miniserver:e}:{}})}async function Ht(r,e,t){return r.callWS({type:"loxone/set_entity_enabled",entity_id:e,enabled:t})}async function Rt(r,e){return r.callWS({type:"loxone/get_areas",...e?{miniserver:e}:{}})}async function Tt(r,e){await r.callService("loxone","sync_areas",{create_areas:e})}async function zt(r){await r.callService("loxone","sync_device_names")}async function Mt(r,e){return r.callWS({type:"loxone/get_bridges",...e?{miniserver:e}:{}})}async function Pt(r,e,t,s){return r.callWS({type:"loxone/add_bridge",entity_id:e,loxone_uuid:t,...s?{miniserver:s}:{}})}async function It(r,e,t){return r.callWS({type:"loxone/remove_bridge",entity_id:e,...t?{miniserver:t}:{}})}async function Ot(r,e){return r.callWS({type:"loxone/get_status",...e?{miniserver:e}:{}})}async function Ut(r,e){return r.callWS({type:"loxone/get_structure_diff",...e?{miniserver:e}:{}})}async function Nt(r,e,t,s){return r.callWS({type:"loxone/send_command",uuid:e,command:t,...s?{miniserver:s}:{}})}var x=class extends g{constructor(){super(...arguments);this.refreshKey=0;this._devices=[];this._filter="";this._loading=!0;this._error="";this._sortKey="room";this._sortDir="asc"}connectedCallback(){super.connectedCallback(),this._loadDevices()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._loadDevices()}async _loadDevices(){this._loading=!0,this._error="";try{let t=await I(this.hass,this.miniserverId);this._devices=t.devices}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}get _filteredDevices(){let t=this._devices;if(this._filter){let s=this._filter.toLowerCase();t=t.filter(o=>o.name.toLowerCase().includes(s)||o.type.toLowerCase().includes(s)||o.room.toLowerCase().includes(s)||o.ha_entities.some(i=>i.entity_id.toLowerCase().includes(s)))}return this._sortDevices(t)}_sortDevices(t){let s=this._sortDir==="asc"?1:-1,o=(p,m)=>{let u=0;switch(this._sortKey){case"name":u=p.name.localeCompare(m.name);break;case"type":u=p.type.localeCompare(m.type)||p.name.localeCompare(m.name);break;case"room":u=(p.room||"").localeCompare(m.room||"")||p.name.localeCompare(m.name);break;case"entities":u=p.ha_entities.length-m.ha_entities.length;break}return u*s},i=new Set(t.filter(p=>!p.parent).map(p=>p.uuid)),n=new Map,c=[];for(let p of t)if(p.parent&&i.has(p.parent)){let m=n.get(p.parent)||[];m.push(p),n.set(p.parent,m)}else c.push(p);c.sort(o);for(let p of n.values())p.sort(o);let l=[];for(let p of c){l.push(p);let m=n.get(p.uuid);m&&l.push(...m)}return l}_toggleSort(t){this._sortKey===t?this._sortDir=this._sortDir==="asc"?"desc":"asc":(this._sortKey=t,this._sortDir="asc")}_sortIndicator(t){return this._sortKey!==t?v:a`<span class="sort-arrow"
      >${this._sortDir==="asc"?"\u25B2":"\u25BC"}</span
    >`}async _toggleEntity(t,s){try{await Ht(this.hass,t,s),await this._loadDevices()}catch(o){this._error=o instanceof Error?o.message:String(o)}}render(){if(this._loading)return a`<p class="status">Loading devices…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let t=this._filteredDevices,s=new Set(t.map(c=>c.uuid)),o=new Map;for(let c of this._devices)for(let l of c.ha_entities){let p=l.entity_id.split(".")[0];o.set(p,(o.get(p)||0)+1)}let i=[...o.values()].reduce((c,l)=>c+l,0),n=[...o.entries()].sort((c,l)=>l[1]-c[1]).map(([c,l])=>`${l} ${c}`).join(", ");return a`
      <div class="toolbar">
        <input
          type="search"
          placeholder="Filter by name, type, room, or entity…"
          .value=${this._filter}
          @input=${c=>{this._filter=c.target.value}}
        />
        
      </div>
      <p class="summary">
        <span class="count">${this._devices.length}</span> controls,
        <span class="count">${i}</span> HA entities
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
          ${t.map(c=>a`
              <tr class=${c.parent&&s.has(c.parent)?"sub-control":""}>
                <td>${c.name}</td>
                <td><span class="badge">${c.type}</span></td>
                <td>${c.room||"\u2014"}</td>
                <td>
                  ${c.ha_entities.length===0?a`<span style="color: var(--secondary-text-color)"
                        >—</span
                      >`:c.ha_entities.map(l=>a`
                          <span
                            class="entity-chip ${l.disabled_by?"disabled":""}"
                          >
                            ${l.entity_id}
                            <button
                              class="toggle-btn"
                              title=${l.disabled_by?"Enable":"Disable"}
                              @click=${()=>this._toggleEntity(l.entity_id,!!l.disabled_by)}
                            >
                              ${l.disabled_by?"\u2B1A":"\u2713"}
                            </button>
                          </span>
                        `)}
                </td>
              </tr>
            `)}
        </tbody>
      </table>
    `}};x.styles=y`
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
  `,d([f({attribute:!1})],x.prototype,"hass",2),d([f({type:Number})],x.prototype,"refreshKey",2),d([f({type:String})],x.prototype,"miniserverId",2),d([h()],x.prototype,"_devices",2),d([h()],x.prototype,"_filter",2),d([h()],x.prototype,"_loading",2),d([h()],x.prototype,"_error",2),d([h()],x.prototype,"_sortKey",2),d([h()],x.prototype,"_sortDir",2),x=d([b("devices-view")],x);var $=class extends g{constructor(){super(...arguments);this.refreshKey=0;this._rooms=[];this._haAreas=[];this._loading=!0;this._syncing=!1;this._error="";this._message=""}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let t=await Rt(this.hass,this.miniserverId);this._rooms=t.rooms,this._haAreas=t.ha_areas}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}async _syncAreas(t){this._syncing=!0,this._message="",this._error="";try{await zt(this.hass),await Tt(this.hass,t),this._message=t?"Synced areas and created missing ones.":"Synced devices to existing areas.",await this._load()}catch(s){this._error=s instanceof Error?s.message:String(s)}finally{this._syncing=!1}}render(){if(this._loading)return a`<p class="status">Loading areas…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let t=this._rooms.filter(o=>o.ha_area_id).length,s=this._rooms.length;return a`
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
          ${this._rooms.map(o=>a`
              <tr>
                <td>${o.name}</td>
                <td>
                  ${o.ha_area_name?a`<span class="mapped">${o.ha_area_name}</span>`:a`<span class="unmapped">Not mapped</span>`}
                </td>
                <td>${o.device_count}</td>
              </tr>
            `)}
        </tbody>
      </table>
    `}};$.styles=y`
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
  `,d([f({attribute:!1})],$.prototype,"hass",2),d([f({type:Number})],$.prototype,"refreshKey",2),d([f({type:String})],$.prototype,"miniserverId",2),d([h()],$.prototype,"_rooms",2),d([h()],$.prototype,"_haAreas",2),d([h()],$.prototype,"_loading",2),d([h()],$.prototype,"_syncing",2),d([h()],$.prototype,"_error",2),d([h()],$.prototype,"_message",2),$=d([b("areas-view")],$);var ie=["sensor","binary_sensor","switch","light","number","input_boolean","input_number"],_=class extends g{constructor(){super(...arguments);this.refreshKey=0;this._bridges=[];this._devices=[];this._loading=!0;this._error="";this._message="";this._newEntityId="";this._newLoxoneUuid="";this._entityFilter="";this._loxoneFilter="";this._showEntityDropdown=!1;this._showLoxoneDropdown=!1}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[t,s]=await Promise.all([Mt(this.hass,this.miniserverId),I(this.hass,this.miniserverId)]);this._bridges=t.bridges,this._devices=s.devices}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}get _availableEntities(){let t=new Set(this._bridges.map(i=>i.entity_id)),s=new Set;for(let i of this._devices)for(let n of i.ha_entities)s.add(n.entity_id);let o=[];for(let[i,n]of Object.entries(this.hass.states)){let c=i.split(".")[0];ie.includes(c)&&(s.has(i)||t.has(i)||o.push({entity_id:i,friendly_name:n.attributes.friendly_name||"",domain:c}))}return o.sort((i,n)=>i.domain!==n.domain?i.domain.localeCompare(n.domain):i.entity_id.localeCompare(n.entity_id)),o}get _filteredEntities(){if(!this._entityFilter)return this._availableEntities;let t=this._entityFilter.toLowerCase();return this._availableEntities.filter(s=>s.entity_id.toLowerCase().includes(t)||s.friendly_name.toLowerCase().includes(t))}_groupByKey(t,s){let o=new Map;for(let i of t){let n=s(i),c=o.get(n)||[];c.push(i),o.set(n,c)}return o}get _availableLoxoneControls(){let t=new Set(this._bridges.map(o=>o.loxone_uuid)),s=[];for(let o of this._devices)t.has(o.uuid)||s.push({uuid:o.uuid,name:o.name,type:o.type,room:o.room||"\u2014"});return s.sort((o,i)=>o.room!==i.room?o.room.localeCompare(i.room):o.name.localeCompare(i.name)),s}get _filteredLoxoneControls(){if(!this._loxoneFilter)return this._availableLoxoneControls;let t=this._loxoneFilter.toLowerCase();return this._availableLoxoneControls.filter(s=>s.name.toLowerCase().includes(t)||s.type.toLowerCase().includes(t)||s.room.toLowerCase().includes(t))}_onEntityFocus(){this._showEntityDropdown=!0}_onEntityBlur(){setTimeout(()=>{this._showEntityDropdown=!1},200)}_selectEntity(t){this._newEntityId=t,this._entityFilter=t,this._showEntityDropdown=!1}_onLoxoneFocus(){this._showLoxoneDropdown=!0}_onLoxoneBlur(){setTimeout(()=>{this._showLoxoneDropdown=!1},200)}_selectLoxone(t,s){this._newLoxoneUuid=t,this._loxoneFilter=s,this._showLoxoneDropdown=!1}async _addBridge(){if(!(!this._newEntityId||!this._newLoxoneUuid)){this._error="",this._message="";try{await Pt(this.hass,this._newEntityId,this._newLoxoneUuid,this.miniserverId),this._message=`Bridge added: ${this._newEntityId}`,this._newEntityId="",this._newLoxoneUuid="",this._entityFilter="",this._loxoneFilter="",await this._load()}catch(t){this._error=t instanceof Error?t.message:String(t)}}}async _removeBridge(t){this._error="",this._message="";try{await It(this.hass,t,this.miniserverId),this._message=`Bridge removed: ${t}`,await this._load()}catch(s){this._error=s instanceof Error?s.message:String(s)}}render(){if(this._loading)return a`<p class="status">Loading bridges…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;let t=this._filteredEntities,s=this._groupByKey(t,n=>n.domain),o=this._filteredLoxoneControls,i=this._groupByKey(o,n=>n.room);return a`
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
                    ${t.length===0?a`<div class="combo-empty">No matching entities</div>`:Array.from(s.entries()).map(([n,c])=>a`
                            <div class="combo-group">${n}</div>
                            ${c.map(l=>a`
                                <div
                                  class="combo-option"
                                  @mousedown=${p=>{p.preventDefault(),this._selectEntity(l.entity_id)}}
                                >
                                  <span>${l.entity_id}</span>
                                  ${l.friendly_name?a`<span class="secondary"
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
              @input=${n=>{this._loxoneFilter=n.target.value,this._newLoxoneUuid="",this._showLoxoneDropdown=!0}}
              @focus=${this._onLoxoneFocus}
              @blur=${this._onLoxoneBlur}
              autocomplete="off"
            />
            ${this._showLoxoneDropdown?a`
                  <div class="combo-dropdown">
                    ${o.length===0?a`<div class="combo-empty">No matching controls</div>`:Array.from(i.entries()).map(([n,c])=>a`
                            <div class="combo-group">${n}</div>
                            ${c.map(l=>a`
                                <div
                                  class="combo-option"
                                  @mousedown=${p=>{p.preventDefault(),this._selectLoxone(l.uuid,l.name)}}
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
      ${this._message?a`<p class="message">${this._message}</p>`:""}
      ${this._bridges.length===0?a`<p class="empty">No device bridges configured.</p>`:a`
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
                ${this._bridges.map(n=>{let c=this.hass.states[n.entity_id],l=c?c.state:"unavailable",p=!c||l==="unavailable"||l==="unknown"?"state-warn":"";return a`
                    <tr>
                      <td>${n.entity_id}</td>
                      <td>
                        <span class="state-value ${p}"
                          >${l}</span
                        >
                      </td>
                      <td class="direction">→</td>
                      <td>${n.loxone_name||n.loxone_uuid}</td>
                      <td><span class="badge">${n.loxone_type}</span></td>
                      <td>
                        <button
                          class="danger"
                          @click=${()=>this._removeBridge(n.entity_id)}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  `})}
              </tbody>
            </table>
          `}
    `}};_.styles=y`
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
  `,d([f({attribute:!1})],_.prototype,"hass",2),d([f({type:Number})],_.prototype,"refreshKey",2),d([f({type:String})],_.prototype,"miniserverId",2),d([h()],_.prototype,"_bridges",2),d([h()],_.prototype,"_devices",2),d([h()],_.prototype,"_loading",2),d([h()],_.prototype,"_error",2),d([h()],_.prototype,"_message",2),d([h()],_.prototype,"_newEntityId",2),d([h()],_.prototype,"_newLoxoneUuid",2),d([h()],_.prototype,"_entityFilter",2),d([h()],_.prototype,"_loxoneFilter",2),d([h()],_.prototype,"_showEntityDropdown",2),d([h()],_.prototype,"_showLoxoneDropdown",2),_=d([b("bridges-view")],_);var E=class extends g{constructor(){super(...arguments);this.refreshKey=0;this._status=null;this._diff=null;this._loading=!0;this._error=""}connectedCallback(){super.connectedCallback(),this._load()}updated(t){t.has("refreshKey")&&t.get("refreshKey")!==void 0&&this._load()}async _load(){this._loading=!0,this._error="";try{let[t,s]=await Promise.all([Ot(this.hass,this.miniserverId),Ut(this.hass,this.miniserverId).catch(()=>null)]);this._status=t,this._diff=s}catch(t){this._error=t instanceof Error?t.message:String(t)}finally{this._loading=!1}}render(){if(this._loading)return a`<p class="status">Loading status…</p>`;if(this._error)return a`<p class="status error">Error: ${this._error}</p>`;if(!this._status)return a`<p class="status">No status available.</p>`;let t=this._status,s=t.connection_state==="connected"?"conn-connected":t.connection_state==="reconnecting"?"conn-reconnecting":"conn-disconnected",o=t.entities_without_state.length;return a`
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
              ${o===0?`All ${t.entities_enabled} enabled entities have state`:a`${o} of ${t.entities_enabled} enabled
                    entities missing state:
                    <br />
                    ${t.entities_without_state.slice(0,10).join(", ")}${o>10?` \u2026 and ${o-10} more`:""}`}
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
    `}_renderStructureDiff(){let t=this._diff;if(!t||!t.has_diff)return a`
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
      `;let s=t.added.length+t.removed.length+t.changed.length,o=t.timestamp?new Date(t.timestamp).toLocaleString(this.hass.language||"en"):"Unknown";return a`
      <h3 class="diagnostics-title" style="margin-top:24px">
        Structure Changes
        <span style="font-weight:400;font-size:12px;color:var(--secondary-text-color)">
          — ${s} change${s!==1?"s":""} at ${o}
        </span>
      </h3>
      <div class="diag-card">
        ${t.added.length>0?a`
              <div class="diag-item">
                <span class="diag-icon" style="color:var(--success-color,#4caf50)">+</span>
                <div>
                  <div class="diag-label">Added (${t.added.length})</div>
                  <div class="diag-detail">
                    ${t.added.map(i=>a`<div>${i.name} <span style="opacity:0.6">(${i.type})</span> — ${i.room||"no room"}</div>`)}
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
                    ${t.removed.map(i=>a`<div>${i.name} <span style="opacity:0.6">(${i.type})</span> — ${i.room||"no room"}</div>`)}
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
                    ${t.changed.map(i=>a`<div>${i.old.name} → ${i.new.name} <span style="opacity:0.6">(${i.new.type})</span></div>`)}
                  </div>
                </div>
              </div>
            `:""}
      </div>
    `}};E.styles=y`
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
    
  `,d([f({attribute:!1})],E.prototype,"hass",2),d([f({type:Number})],E.prototype,"refreshKey",2),d([f({type:String})],E.prototype,"miniserverId",2),d([h()],E.prototype,"_status",2),d([h()],E.prototype,"_diff",2),d([h()],E.prototype,"_loading",2),d([h()],E.prototype,"_error",2),E=d([b("status-view")],E);var V=500,S=class extends g{constructor(){super(...arguments);this._events=[];this._paused=!1;this._filter="";this._connected=!1;this._error="";this._pendingEvents=[]}connectedCallback(){super.connectedCallback(),this._subscribe()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe()}updated(t){t.has("miniserverId")&&(this._unsubscribe(),this._events=[],this._subscribe())}async _subscribe(){this._error="";try{this._unsub=await this.hass.connection.subscribeMessage(t=>{let s=t;if(s.events){if(this._paused){this._pendingEvents.push(...s.events),this._pendingEvents.length>V&&(this._pendingEvents=this._pendingEvents.slice(-V));return}this._events=[...s.events,...this._events].slice(0,V)}},{type:"loxone/subscribe_events",...this.miniserverId?{miniserver:this.miniserverId}:{}}),this._connected=!0}catch(t){this._error=t instanceof Error?t.message:String(t),this._connected=!1}}_unsubscribe(){this._unsub&&(this._unsub(),this._unsub=void 0),this._connected=!1}_togglePause(){this._paused=!this._paused,!this._paused&&this._pendingEvents.length>0&&(this._events=[...this._pendingEvents,...this._events].slice(0,V),this._pendingEvents=[])}_clear(){this._events=[],this._pendingEvents=[]}_onFilterInput(t){this._filter=t.target.value.toLowerCase()}_formatTime(t){try{return new Date(t).toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:1})}catch{return t}}_formatValue(t){return t==null?"\u2014":typeof t=="number"?Number.isInteger(t)?String(t):t.toFixed(2):typeof t=="object"?JSON.stringify(t):String(t)}render(){let t=this._filter,s=t?this._events.filter(o=>o.name.toLowerCase().includes(t)||o.room.toLowerCase().includes(t)||o.uuid.toLowerCase().includes(t)):this._events;return a`
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
        <span class="count">${s.length} event${s.length!==1?"s":""}</span>
        ${this._error?a`<span class="error">${this._error}</span>`:""}
      </div>
      <div class="log-container">
        ${s.length===0?a`<div class="empty">
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
                    ${s.map(o=>a`
                        <tr>
                          <td class="ts">${this._formatTime(o.timestamp)}</td>
                          <td class="name">${o.name||"\u2014"}</td>
                          <td class="room">${o.room||"\u2014"}</td>
                          <td class="value">${this._formatValue(o.value)}</td>
                          <td class="uuid" title=${o.uuid}>${o.uuid}</td>
                        </tr>
                      `)}
                  </tbody>
                </table>
              </div>
            `}
      </div>
    `}};S.styles=y`
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
  `,d([f({attribute:!1})],S.prototype,"hass",2),d([f({type:String})],S.prototype,"miniserverId",2),d([h()],S.prototype,"_events",2),d([h()],S.prototype,"_paused",2),d([h()],S.prototype,"_filter",2),d([h()],S.prototype,"_connected",2),d([h()],S.prototype,"_error",2),S=d([b("monitor-view")],S);var Kt="loxone_console_history",ht=50,w=class extends g{constructor(){super(...arguments);this._uuid="";this._command="";this._sending=!1;this._history=[];this._devices=[];this._suggestions=[];this._selectedDevice=null}connectedCallback(){super.connectedCallback(),this._loadHistory(),this._loadDevices()}updated(t){t.has("miniserverId")&&this._loadDevices()}_loadHistory(){try{let t=localStorage.getItem(Kt);t&&(this._history=JSON.parse(t))}catch{}}_saveHistory(){try{localStorage.setItem(Kt,JSON.stringify(this._history.slice(-ht)))}catch{}}async _loadDevices(){try{let t=await I(this.hass,this.miniserverId);this._devices=t.devices}catch{}}_onUuidInput(t){this._uuid=t.target.value,this._selectedDevice=null;let s=this._uuid.toLowerCase();s.length>=2?this._suggestions=this._devices.filter(o=>o.name.toLowerCase().includes(s)||o.uuid.toLowerCase().includes(s)||o.type.toLowerCase().includes(s)).slice(0,8):this._suggestions=[]}_selectSuggestion(t){this._uuid=t.uuid,this._selectedDevice=t,this._suggestions=[]}_getCommandHints(){if(!this._selectedDevice)return[];switch(this._selectedDevice.type){case"Switch":return["On","Off","pulse"];case"Dimmer":case"EIBDimmer":return["On","Off","0","50","100"];case"Slider":return["0","50","100"];case"Jalousie":return["up","down","fullUp","fullDown","shade","stop"];case"Gate":return["open","close","stop"];case"LightController":case"LightControllerV2":return["on","off","plus","minus","changeTo/1"];case"IRoomController":case"IRoomControllerV2":return["setComfortTemperature/21","setEcoOffset/2","operatingMode/0"];case"Alarm":return["on","off","delayedOn"];case"ColorPickerV2":return["hsv(0,100,100)","temp(2700,100)"];case"TextInput":return[];default:return["On","Off","pulse"]}}_applyHint(t){this._command=t}_onCommandInput(t){this._command=t.target.value}_onKeyDown(t){t.key==="Enter"&&this._uuid&&this._command&&this._send(),t.key==="Escape"&&(this._suggestions=[])}async _send(){if(!this._uuid||!this._command||this._sending)return;this._sending=!0,this._suggestions=[];let t=new Date().toLocaleTimeString(this.hass.language||"en",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),s=this._selectedDevice?.name,o=this._selectedDevice?.uuid||this._uuid;try{let i=await Nt(this.hass,o,this._command,this.miniserverId);this._history=[...this._history,{uuid:o,name:s,command:this._command,result:"OK",ok:!0,timestamp:t}].slice(-ht)}catch(i){let n=i instanceof Error?i.message:String(i);this._history=[...this._history,{uuid:o,name:s,command:this._command,result:n,ok:!1,timestamp:t}].slice(-ht)}finally{this._sending=!1,this._saveHistory()}}_clearHistory(){this._history=[],this._saveHistory()}render(){return a`
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
    `}};w.styles=y`
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
  `,d([f({attribute:!1})],w.prototype,"hass",2),d([f({type:String})],w.prototype,"miniserverId",2),d([h()],w.prototype,"_uuid",2),d([h()],w.prototype,"_command",2),d([h()],w.prototype,"_sending",2),d([h()],w.prototype,"_history",2),d([h()],w.prototype,"_devices",2),d([h()],w.prototype,"_suggestions",2),d([h()],w.prototype,"_selectedDevice",2),w=d([b("console-view")],w);var A=class extends g{constructor(){super(...arguments);this._activeTab="devices";this._refreshKey=0;this._entries=[]}connectedCallback(){super.connectedCallback(),this._loadEntries()}async _loadEntries(){try{let t=await Dt(this.hass);this._entries=t.entries,!this._selectedMiniserver&&this._entries.length>0&&(this._selectedMiniserver=this._entries[0].miniserver)}catch{}}_setTab(t){this._activeTab=t}_refresh(){this._refreshKey++}_onEntryChange(t){let s=t.target;this._selectedMiniserver=s.value,this._refreshKey++}render(){let t=this._entries.length>1;return a`
      <div class="header">
        <div class="header-left">
          <h1>Loxone</h1>
          ${t?a`
                <select
                  class="entry-select"
                  .value=${this._selectedMiniserver??""}
                  @change=${this._onEntryChange}
                >
                  ${this._entries.map(s=>a`
                      <option value=${s.miniserver}>
                        ${s.name||s.title||s.host}
                      </option>
                    `)}
                </select>
              `:v}
        </div>
        <button class="refresh-btn" @click=${this._refresh}>↻ Refresh</button>
      </div>
      <div class="tabs">
        ${["devices","areas","bridges","monitor","console","status"].map(s=>a`
            <div
              class="tab ${this._activeTab===s?"active":""}"
              @click=${()=>this._setTab(s)}
            >
              ${s.charAt(0).toUpperCase()+s.slice(1)}
            </div>
          `)}
      </div>
      ${this._renderTab()}
    `}_renderTab(){let t=this._refreshKey,s=this._selectedMiniserver;switch(this._activeTab){case"devices":return a`<devices-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${s}></devices-view>`;case"areas":return a`<areas-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${s}></areas-view>`;case"bridges":return a`<bridges-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${s}></bridges-view>`;case"monitor":return a`<monitor-view .hass=${this.hass} .miniserverId=${s}></monitor-view>`;case"console":return a`<console-view .hass=${this.hass} .miniserverId=${s}></console-view>`;case"status":return a`<status-view .hass=${this.hass} .refreshKey=${t} .miniserverId=${s}></status-view>`}}};A.styles=y`
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
  `,d([f({attribute:!1})],A.prototype,"hass",2),d([h()],A.prototype,"_activeTab",2),d([h()],A.prototype,"_refreshKey",2),d([h()],A.prototype,"_entries",2),d([h()],A.prototype,"_selectedMiniserver",2),A=d([b("loxone-panel")],A);export{A as LoxonePanel};
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
