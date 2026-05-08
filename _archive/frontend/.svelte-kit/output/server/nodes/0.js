

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/0.DuzBrEP1.js","_app/immutable/chunks/BFz-wl6Q.js","_app/immutable/chunks/CwfvWAfg.js","_app/immutable/chunks/CXhweGeG.js"];
export const stylesheets = [];
export const fonts = [];
