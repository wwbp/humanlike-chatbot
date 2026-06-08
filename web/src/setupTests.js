// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom doesn't implement scrollIntoView — stub it so components that call
// endRef.current?.scrollIntoView() don't throw.
window.HTMLElement.prototype.scrollIntoView = vi.fn();
