// Define the checkbox component in a separate scope
function checkboxComponent() {
  return {
    // Define items inside the component
    hello: "World",
    items: [
      { label: 'Professional Experience', val: 'exp' },
      { label: 'Publications', val: 'pub' },
      { label: 'Patents', val: 'pat' },
      { label: 'Education', val: 'edu' },
      { label: 'Micro-credits', val: 'mcr' },
      { label: 'Skills', val: 'skl' },
      { label: 'Languages', val: 'lng' },
    ],
    checkeditems: [],
    lang:"en"
    //,

    //init() {this.items.forEach(item => { this.checkeditems[item.value] = false;});}
  };
}

document.addEventListener('alpine:init', () => {
  console.log("Registered");
  Alpine.data('checkboxComponent', checkboxComponent);  // Register with Alpine
});

class ResumeViewer extends HTMLElement {

  static get observedAttributes() {
    return ['lang',"checkeditems"];
  }

  get checkeditems() {
    return this.hasAttribute('checkeditems');
  }

  get lang() {
    return this.hasAttribute('lang');
  }

  set checkeditems(value) {
    console.log("attributeSet")
    this.setAttribute('checkeditems', value);
  }

  set lang(value) {
    console.log("attributeSet")
    this.setAttribute('lang', value);
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }
  
  async connectedCallback() {
    await this._render();
  }

  async attributeChangedCallback(name, oldValue, newValue) {
    console.log("attributeChanged")
    await this._render();
  }

  async _render() {
    try{
        sectionReq = ""
        var sections = this.getAttribute('checkeditems')
        if (sections){
          sections = sections.split(",")
          var sectionReq = ""
          for (let i = 0; i<  sections.length; i++){
              sectionReq += `&sections=${encodeURIComponent(sections[i])}`
          }
        }
        const lang = this.getAttribute('lang') || 'en';
        console.log(sections)

        
        const response = await fetch(`/component?lang=${encodeURIComponent(lang)}`+sectionReq);
        //const response = await fetch(`/component`);
        if (!response.ok) throw new Error('Failed to load component');
        const { html, css,js } = await response.json();
        this.shadowRoot.innerHTML = `    
        <script>${js}</script>    
        <style>${css}</style>
        ${html}
        `;
    }
    catch(err){
        console.error('Error loading component:', err);
        this.shadowRoot.innerHTML = `<p>Error loading component. See console for details.</p>`;
    }
  }
}

customElements.define('resume-viewer', ResumeViewer);