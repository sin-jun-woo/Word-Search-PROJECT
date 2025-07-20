<script>
  import { push } from "svelte-spa-router";
  import { onMount } from "svelte";

  let title = "";
  let description = "";
  let wordsText = "";
  let authToken = null; // 인증 토큰 저장
  let isLoading = true; // 인증 처리 중 로딩 상태
  let authError = null; // 인증 오류 메시지

  // 컴포넌트 마운트 시 관리자 계정으로 자동 로그인/회원가입
  onMount(async () => {
    const adminEmail = "admin@example.com";
    const adminPassword = "adminpassword";

    // 1. 로그인 시도
    let res = await fetch("http://127.0.0.1:8000/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: adminEmail, password: adminPassword }),
    });

    // 2. 로그인 실패 시 (계정 없음), 회원가입 후 다시 로그인
    if (res.status === 400) {
      console.log("관리자 계정이 없어 새로 생성합니다.");
      // 회원가입
      await fetch("http://127.0.0.1:8000/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "admin",
          email: adminEmail,
          password: adminPassword,
        }),
      });

      // 다시 로그인
      res = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: adminEmail, password: adminPassword }),
      });
    }

    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      console.log("✅ 관리자 인증 성공");
    } else {
      authError = "관리자 인증에 실패했습니다. 백엔드 서버를 확인해주세요.";
      console.error("❌ 관리자 인증 실패", await res.text());
    }
    isLoading = false;
  });

  async function createGame() {
    if (!authToken) {
      alert(
        "아직 관리자 인증이 완료되지 않았습니다. 잠시 후 다시 시도해주세요."
      );
      return;
    }

    const wordArray = wordsText
      .split(",")
      .map((w) => w.trim())
      .filter(Boolean);

    const payload = {
      title,
      description,
      word_list: wordArray,
    };

    const res = await fetch("http://127.0.0.1:8000/games", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`, // 인증 헤더 추가
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      console.error("❌ 게임 생성 실패", res.status, await res.text());
      alert(`게임 생성에 실패했습니다. (에러: ${res.status})`);
      return;
    }

    const data = await res.json();
    console.log("✅ 게임 생성 성공:", data);

    // 생성된 게임 ID로 자동 이동 (닉네임은 'Admin'으로 고정)
    push(`/game/${data.id}?nickname=Admin`);
  }
</script>

<h1>🛠 Word Search Maker</h1>

{#if isLoading}
  <p>관리자 인증 중...</p>
{:else if authError}
  <p style="color: red;">{authError}</p>
{:else}
  <div class="form-container">
    <label for="title-input">게임 제목</label>
    <input id="title-input" bind:value={title} placeholder="게임 제목" />

    <label for="desc-input">게임 설명</label>
    <input id="desc-input" bind:value={description} placeholder="게임 설명" />

    <label for="words-input">단어 리스트 (콤마로 구분)</label>
    <input
      id="words-input"
      bind:value={wordsText}
      placeholder="APPLE, BANANA, ORANGE"
    />

    <button on:click={createGame} disabled={!title || !wordsText}
      >게임 생성</button
    >
  </div>
{/if}

<style>
  .form-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
    margin: auto;
  }
  input {
    padding: 8px;
    font-size: 1em;
  }
  button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
</style>
