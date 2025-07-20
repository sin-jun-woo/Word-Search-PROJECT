<script>
  import Router from "svelte-spa-router";
  import Maker from "./pages/Maker.svelte";
  import Lobby from "./pages/Lobby.svelte";
  import Game from "./pages/Game.svelte";

  const routes = {
    "/": Lobby,
    "/maker": Maker,
    "/game/:id": Game,
  };
</script>

<main>
  <Router {routes} />
</main>

<style>
  :global(:root) {
    --background-color: #ffffff;
    --text-color: #213547;
    --text-color-light: #555;
    --text-color-muted: #777;
    --link-color: #4585d7;
    --card-background: #ffffff;
    --card-border: #e0e0e0;
    --button-background: #f9f9f9;
    --button-hover-background: #e9e9e9;
    --input-background: #fff;
    --input-border: #ccc;
    --cell-background: #fff;
    --cell-border: #ddd;
    --game-over-background: #f0f8ff;
    --game-over-border: #cce5ff;
  }

  @media (prefers-color-scheme: dark) {
    :global(:root) {
      --background-color: #121212;
      --text-color: rgba(255, 255, 255, 0.87);
      --text-color-light: rgba(255, 255, 255, 0.7);
      --text-color-muted: rgba(255, 255, 255, 0.5);
      --link-color: #8ab4f8;
      --card-background: #1e1e1e;
      --card-border: #444;
      --button-background: #333;
      --button-hover-background: #444;
      --input-background: #2a2a2a;
      --input-border: #555;
      --cell-background: #2a2a2a;
      --cell-border: #444;
      --game-over-background: #2a2a3a;
      --game-over-border: #444466;
    }
  }

  :global(body) {
    background-color: var(--background-color);
    color: var(--text-color);
    transition:
      background-color 0.2s,
      color 0.2s;
    /* 우리 앱이 라이트/다크 모드를 모두 지원함을 브라우저에 알립니다. */
    color-scheme: light dark;
  }

  :global(a) {
    color: var(--link-color);
  }

  :global(button) {
    background-color: var(--button-background);
    color: var(--text-color);
    border: 1px solid var(--card-border);
  }
  :global(button:hover) {
    background-color: var(--button-hover-background);
  }
</style>
