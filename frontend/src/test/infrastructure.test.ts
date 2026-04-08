import { describe, it, expect } from "vitest";

describe("test infrastructure", () => {
  it("vitest runs with jsdom environment", () => {
    expect(document).toBeDefined();
    expect(window).toBeDefined();
  });

  it("jest-dom matchers are available", () => {
    const div = document.createElement("div");
    div.textContent = "hello";
    document.body.appendChild(div);
    expect(div).toBeInTheDocument();
    document.body.removeChild(div);
  });
});
