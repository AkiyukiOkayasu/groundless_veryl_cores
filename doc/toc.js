// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded affix "><a href="index.html">groundless_veryl_cores</a></li><li class="chapter-item expanded "><div>0.2.0</div></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded "><a href="modules.html">Modules</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="Phaser.html">Phaser</a></li><li class="chapter-item "><a href="PwmSquareOscillator.html">PwmSquareOscillator</a></li><li class="chapter-item "><a href="SawOscillator.html">SawOscillator</a></li><li class="chapter-item "><a href="SawWaveCore.html">SawWaveCore</a></li><li class="chapter-item "><a href="SineOscillator.html">SineOscillator</a></li><li class="chapter-item "><a href="SineOscillatorLerp.html">SineOscillatorLerp</a></li><li class="chapter-item "><a href="SineRomQuarter.html">SineRomQuarter</a></li><li class="chapter-item "><a href="SineRomQuarterDual.html">SineRomQuarterDual</a></li><li class="chapter-item "><a href="SineWaveCore.html">SineWaveCore</a></li><li class="chapter-item "><a href="SineWaveLerpCore.html">SineWaveLerpCore</a></li><li class="chapter-item "><a href="SpiMaster.html">SpiMaster</a></li><li class="chapter-item "><a href="SquareWaveCore.html">SquareWaveCore</a></li><li class="chapter-item "><a href="TriangleOscillator.html">TriangleOscillator</a></li><li class="chapter-item "><a href="TriangleWaveCore.html">TriangleWaveCore</a></li><li class="chapter-item "><a href="WhiteNoise.html">WhiteNoise</a></li><li class="chapter-item "><a href="midi_rx.html">midi_rx</a></li><li class="chapter-item "><a href="uart_rx.html">uart_rx</a></li></ol></li><li class="chapter-item expanded "><a href="proto_modules.html">Module Prototypes</a></li><li class="chapter-item expanded "><a href="interfaces.html">Interfaces</a></li><li class="chapter-item expanded "><a href="packages.html">Packages</a><a class="toggle"><div>❱</div></a></li><li><ol class="section"><li class="chapter-item "><a href="FixedPoint.html">FixedPoint</a></li><li class="chapter-item "><a href="Phase.html">Phase</a></li></ol></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString().split("#")[0].split("?")[0];
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
