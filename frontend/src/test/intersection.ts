import { act } from '@testing-library/react';

const observers = new Set<FakeIntersectionObserver>();

// jsdom has no layout, so nothing ever scrolls into view: tests say when the end of a list is visible.
export class FakeIntersectionObserver {
  private readonly targets = new Set<Element>();

  constructor(private readonly callback: IntersectionObserverCallback) {}

  observe(target: Element) {
    this.targets.add(target);
    observers.add(this);
  }

  unobserve(target: Element) {
    this.targets.delete(target);
  }

  disconnect() {
    this.targets.clear();
    observers.delete(this);
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }

  reveal() {
    const entries = [...this.targets].map(
      // Only the fields the app reads; the rest of the entry describes layout jsdom does not have.
      (target) => ({ target, isIntersecting: true }) as IntersectionObserverEntry,
    );
    // The observer argument is unused by the app; jsdom offers no real one to pass.
    this.callback(entries, this as unknown as IntersectionObserver);
  }
}

/** Scrolls every observed list end into view. */
export function revealListEnds() {
  act(() => {
    for (const observer of [...observers]) {
      observer.reveal();
    }
  });
}
