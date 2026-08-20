function Icon({ name, size = 16, color, style }) {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!ref.current || !window.lucide || !lucide[name]) return;
    ref.current.innerHTML = lucide.createElement(lucide[name]).outerHTML;
    const svg = ref.current.querySelector("svg");
    if (svg) { svg.setAttribute("width", size); svg.setAttribute("height", size); }
  }, [name, size]);
  return <span ref={ref} style={{ display: "inline-flex", color, ...style }} />;
}
Object.assign(window, { Icon });
