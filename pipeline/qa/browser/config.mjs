// Shared config for QA scripts targeting prod v2/uk.
export const PROD_BASE = "https://episodes-zymk.onrender.com/v2/uk";
export const EPISODE_URL = (id) => {
  const n = String(id).padStart(3, "0");
  return `${PROD_BASE}/ep_${n}/ep_${n}.html`;
};
export const TOTAL_EPISODES = 40;
export const VIEWPORT = { width: 412, height: 915 }; // mobile-first like real player
export const DESKTOP_VIEWPORT = { width: 1280, height: 900 };
