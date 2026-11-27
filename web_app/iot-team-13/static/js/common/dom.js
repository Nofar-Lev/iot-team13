// Small helpers for building page elements.

/** A new element with a class and, optionally, text inside it. */
export function el(tagName, className = "", text = null) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (text !== null) element.textContent = text;
  return element;
}

/** Remove everything inside an element. */
export function clear(element) {
  element.replaceChildren();
}
