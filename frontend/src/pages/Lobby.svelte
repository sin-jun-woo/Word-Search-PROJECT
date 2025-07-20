<script>
  import { push, link } from "svelte-spa-router";
  import { onMount } from "svelte";

  let nickname = "";
  let games = [];
  let isLoading = true;
  let error = null;

  onMount(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/games");
      if (!res.ok) throw new Error("게임 목록을 불러오는 데 실패했습니다.");
      games = await res.json();
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  });

  function startGame(gameId) {
    if (!nickname.trim()) return alert("닉네임을 입력해주세요!");
    const encodedNickname = encodeURIComponent(nickname.trim());
    push(`/game/${gameId}?nickname=${encodedNickname}`);
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString(); // YYYY-MM-DD HH:mm:ss
  }
</script>

<h1>🎮 Word Search Lobby</h1>
<p>게임에 참여할 닉네임을 입력해주세요</p>

<div class="nickname-input">
  <input bind:value={nickname} placeholder="닉네임 입력" />
</div>

<p>
  <a href="/maker" use:link>게임 생성하기 (어드민)</a>
</p>

<hr />

<h2>게임 목록</h2>

{#if isLoading}
  <p>게임 목록을 불러오는 중...</p>
{:else if error}
  <p style="color: red;">{error}</p>
{:else if games.length === 0}
  <p>플레이할 수 있는 게임이 없습니다. 새 게임을 만들어보세요!</p>
{:else}
  <div class="game-list">
    {#each games as game}
      <div class="game-card">
        <h3>{game.title}</h3>
        <p class="description">{game.description || "설명이 없습니다."}</p>
        <div class="meta">
          <span>제작자: {game.created_by || "알 수 없음"}</span>
          <span>제작일: {formatDate(game.create_at)}</span>
        </div>
        <button on:click={() => startGame(game.id)}>플레이</button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .nickname-input {
    margin-bottom: 20px;
  }
  .nickname-input input {
    background-color: var(--input-background);
    border: 1px solid var(--input-border);
    color: var(--text-color);
  }
  .game-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }
  .game-card {
    border: 1px solid var(--card-border);
    background-color: var(--card-background);
    padding: 15px;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
  }
  .game-card h3 {
    margin-top: 0;
  }
  .game-card .description {
    flex-grow: 1;
    color: var(--text-color-light);
    font-size: 0.9em;
  }
  .game-card .meta {
    font-size: 0.8em;
    color: var(--text-color-muted);
    margin-top: 10px;
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
  }
  button {
    width: 100%;
  }
</style>
