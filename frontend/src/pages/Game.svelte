<script>
  export let params;
  import { onMount, onDestroy } from "svelte";
  import { querystring, push } from "svelte-spa-router";

  // --- 상태 변수 (State Variables) ---
  let gameData = null;
  let timer = 0;
  let interval = null;
  let ws = null;
  let allSubmissions = []; // 서버에서 받은 모든 결과 기록
  let isGameFinished = false; // 게임 완료 상태

  // URL에서 닉네임 가져오기
  $: urlParams = new URLSearchParams($querystring);
  $: nickname = urlParams.get("nickname") || "익명 플레이어";

  // --- 반응형 파생 변수 (Reactive Derived State) ---
  // gameData가 로드되면 자동으로 파생 변수들이 계산됩니다.
  $: gridLetters = gameData ? JSON.parse(gameData.grid) : [];
  $: gridSize = gameData ? gameData.grid_size : 10;
  $: wordList = gameData ? JSON.parse(gameData.word_list) : [];
  $: maxWordLen = gameData ? Math.max(...wordList.map((w) => w.length)) : 0;

  // 선택 상태 & 찾은 단어 저장
  $: selectedCells = Array(gridSize * gridSize).fill(false);
  let foundWords = new Set();

  // allSubmissions이 변경될 때마다 리더보드를 다시 계산합니다.
  $: leaderboard = (() => {
    const totalWords = wordList.length;
    const playerBestScores = new Map();
    for (const submission of allSubmissions) {
      try {
        const playerName = submission.player_name;
        // 서버에서 받은 found_words는 JSON 문자열이므로 파싱합니다.
        const words = JSON.parse(submission.found_words);
        const score = words.length;
        const time = submission.time_token;
        const finished = totalWords > 0 && score === totalWords;

        const currentBest = playerBestScores.get(playerName);

        // 기존 기록이 없거나, 새 기록이 더 좋으면 (점수가 높거나, 점수가 같으면 시간이 짧으면) 업데이트
        if (
          !currentBest ||
          score > currentBest.score ||
          (score === currentBest.score && time < currentBest.time)
        ) {
          playerBestScores.set(playerName, {
            name: playerName,
            score,
            time,
            finished,
          });
        }
      } catch (e) {
        console.error("결과를 처리하는 중 오류 발생:", submission, e);
      }
    }

    // Map을 배열로 변환하고 점수(내림차순), 시간(오름차순)으로 정렬
    return Array.from(playerBestScores.values()).sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.time - b.time;
    });
  })();

  // --- 생명주기 함수 (Lifecycle Functions) ---
  onMount(async () => {
    const res = await fetch(`http://127.0.0.1:8000/games/${params.id}`);
    if (res.ok) gameData = await res.json();

    // 기존 게임 결과 불러오기
    const resultsRes = await fetch(
      `http://127.0.0.1:8000/games/${params.id}/results`
    );
    if (resultsRes.ok) allSubmissions = await resultsRes.json();

    interval = setInterval(() => {
      timer++;
    }, 1000);

    // WebSocket 연결
    ws = new WebSocket(`ws://127.0.0.1:8000/ws/games/${params.id}/results`);
    ws.onopen = () => console.log("✅ WebSocket 연결 성공");
    ws.onmessage = (event) => {
      console.log("📥 WebSocket 메시지 수신:", event.data);
      try {
        const newSubmission = JSON.parse(event.data);
        // 새 결과가 도착하면 allSubmissions 배열에 추가 (leaderboard는 자동으로 업데이트됨)
        allSubmissions = [...allSubmissions, newSubmission];
      } catch (e) {
        console.error("WebSocket 메시지 파싱 오류:", e);
      }
    };
    ws.onclose = () => console.log("🔌 WebSocket 연결 종료");
    ws.onerror = (error) => console.error("❌ WebSocket 오류:", error);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
    if (ws) ws.close();
  });

  // --- 이벤트 핸들러 및 게임 로직 ---
  let selectedPath = []; // 클릭한 인덱스

  function handleCellClick(index) {
    // 게임이 끝났으면 클릭 무시
    if (isGameFinished) return;

    // 이미 정답으로 처리된 셀은 무시
    if (selectedCells[index] === "found") return;

    // 같은 셀 다시 클릭하면 선택 취소 (토글)
    if (selectedPath.includes(index)) {
      selectedPath = selectedPath.filter((i) => i !== index);
    } else {
      selectedPath.push(index);
    }

    // 선택된 글자 업데이트
    const selectedWord = selectedPath.map((i) => gridLetters[i]).join("");
    console.log("선택:", selectedWord);

    // 정답일 때
    if (wordList.includes(selectedWord)) {
      alert(`✅ ${selectedWord} 찾았다!`);
      foundWords.add(selectedWord);
      foundWords = foundWords; // Set의 변경을 Svelte에 알림

      // 서버에 결과 전송
      sendResultToServer();

      // 선택된 셀을 영구적으로 found 처리
      selectedPath.forEach((i) => (selectedCells[i] = "found"));

      // 선택 상태 초기화
      selectedPath = [];

      // 게임 완료 여부 확인
      checkGameComplete();
    } else {
      // 선택한 글자가 너무 길면 틀린 걸로 간주하고 초기화
      if (maxWordLen > 0 && selectedWord.length >= maxWordLen) {
        alert("❌ 틀렸습니다!");
        resetSelection();
      }
    }

    // 선택된 셀 표시 (selected or found)를 위해 selectedCells 배열 업데이트
    selectedCells = selectedCells.map((v, i) =>
      selectedPath.includes(i) ? "selected" : v === "found" ? "found" : false
    );
  }

  // 선택 초기화 함수
  function resetSelection() {
    selectedPath = [];
    selectedCells = selectedCells.map((v) => (v === "found" ? "found" : false));
  }

  // 게임 완료 체크 함수
  function checkGameComplete() {
    // wordList가 존재하고, 찾은 단어 수가 전체 단어 수와 같으면 게임 클리어
    if (wordList.length > 0 && foundWords.size === wordList.length) {
      if (interval) clearInterval(interval); // 타이머 정지
      isGameFinished = true; // 게임 완료 상태로 변경

      // UI가 업데이트될 시간을 약간 준 후 알림 표시
      setTimeout(() => {
        alert(
          `🎉 게임 클리어! 최종 기록: ${timer}초\n\n다른 플레이어들의 현황판도 업데이트됩니다.`
        );
      }, 100);
    }
  }

  // 서버에 게임 결과를 POST로 전송하는 함수
  async function sendResultToServer() {
    const payload = {
      player_name: nickname,
      time_token: timer,
      found_words: Array.from(foundWords),
    };

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/games/${params.id}/results`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      if (!res.ok) {
        console.error("결과 전송 실패:", res.statusText);
      }
    } catch (error) {
      console.error("결과 전송 중 네트워크 오류:", error);
    }
  }

  // 홈으로 이동하는 함수
  function goToHome() {
    push("/");
  }

  // 현재 게임 링크를 복사하는 함수
  function copyGameLink() {
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => {
        alert("게임 링크가 클립보드에 복사되었습니다!");
      })
      .catch((err) => {
        console.error("링크 복사 실패:", err);
      });
  }
</script>

{#if gameData}
  <div class="header">
    <h1>🎮 {gameData.title}</h1>
    <p>{gameData.description}</p>
    <p>
      ⏳ {Math.floor(timer / 60)}:{timer % 60 < 10
        ? `0${timer % 60}`
        : timer % 60}
    </p>
  </div>

  <div class="game-container">
    <!-- 좌측: 단어 리스트 -->
    <div class="game-left">
      <h3>📜 찾아야 할 단어</h3>
      <ul>
        {#each wordList as word}
          <li class={foundWords.has(word) ? "done" : ""}>
            {foundWords.has(word) ? "✅" : "⬜️"}
            {word}
          </li>
        {/each}
      </ul>
    </div>

    <!-- 중앙: 게임판 -->
    <div class="game-center" style="--grid-size: {gridSize}">
      {#each gridLetters as letter, i}
        <div
          role="button"
          tabindex="0"
          class="cell
    {selectedCells[i] === 'found' ? 'found' : ''} 
    {selectedCells[i] === 'selected' ? 'selected' : ''}"
          on:click={() => handleCellClick(i)}
          on:keydown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault(); // 스페이스바 누를 때 화면 스크롤 방지
              handleCellClick(i);
            }
          }}
        >
          {gridLetters[i]}
        </div>
      {/each}
    </div>

    <!-- 우측: 현황판 -->
    <div class="game-right">
      <h3>🏆 현황판</h3>
      <p class="my-score">
        <strong>내 점수:</strong>
        {foundWords.size} / {wordList.length}개
      </p>
      <hr />
      <ol class="leaderboard">
        {#each leaderboard as player, i}
          <li class:top-rank={i < 3}>
            <span class="rank">
              {#if i === 0}🥇{:else if i === 1}🥈{:else if i === 2}🥉{:else}{i +
                  1}.{/if}
            </span>
            <span class="name">{player.name}</span>
            <span class="score">
              {#if player.finished}
                <span class="final-time">🏁 {player.time}초</span>
              {:else}
                {player.score}점
              {/if}
            </span>
          </li>
        {/each}
      </ol>
    </div>
  </div>

  {#if isGameFinished}
    <div class="game-over-controls">
      <h3>게임 종료!</h3>
      <p>
        수고하셨습니다! 다른 게임을 플레이하거나, 이 게임을 친구에게
        공유해보세요.
      </p>
      <div class="buttons">
        <button on:click={goToHome}>🏠 홈으로 나가기</button>
        <button on:click={copyGameLink}>🔗 게임 링크 복사</button>
      </div>
    </div>
  {/if}
{:else}
  <p>⏳ 게임 데이터를 불러오는 중...</p>
{/if}

<style>
  .game-container {
    display: grid;
    grid-template-columns: 200px 1fr 200px;
    gap: 20px;
    padding: 20px;
  }

  .game-left,
  .game-right {
    background: var(--card-background);
    padding: 10px;
    border-radius: 10px;
    border: 1px solid var(--card-border);
  }

  .game-left li.done {
    text-decoration: line-through;
    color: green;
    font-weight: bold;
  }

  .game-center {
    display: grid;
    grid-template-columns: repeat(var(--grid-size, 10), 40px);
    gap: 5px;
    justify-content: center;
  }

  .cell {
    width: 40px;
    height: 40px;
    background: var(--cell-background);
    border: 1px solid var(--cell-border);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: bold;
    transition: background 0.2s;
  }

  .cell.found {
    background: lightgreen;
    /* 찾은 단어의 셀은 클릭 비활성화 */
    pointer-events: none;
  }
  .cell.selected {
    background: yellow;
  }

  .header {
    text-align: center;
    margin-bottom: 20px;
  }

  .my-score {
    margin-bottom: 15px;
    font-size: 1.1em;
  }

  .leaderboard {
    list-style: none;
    padding: 0;
  }

  .leaderboard li {
    display: flex;
    align-items: center;
    padding: 8px 4px;
    border-bottom: 1px solid #eee;
    transition: background-color 0.2s;
  }

  .leaderboard li.top-rank {
    font-weight: bold;
  }

  .leaderboard .rank {
    width: 40px;
    text-align: center;
    font-size: 1.2em;
  }
  .leaderboard .name {
    flex-grow: 1;
  }
  .leaderboard .score {
    font-family: monospace;
  }

  .final-time {
    color: #2e8b57; /* SeaGreen */
    font-weight: bold;
  }

  .game-over-controls {
    margin-top: 30px;
    padding: 20px;
    text-align: center;
    background-color: var(--game-over-background);
    border-radius: 8px;
    border: 1px solid var(--game-over-border);
  }

  .game-over-controls h3 {
    margin-top: 0;
  }

  .game-over-controls .buttons {
    margin-top: 15px;
  }

  .game-over-controls button {
    margin: 0 10px;
  }
</style>
