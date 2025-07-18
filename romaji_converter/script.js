const romajiOutput = document.getElementById('romaji-output');
const convertButton = document.getElementById('convert-button');

// ボタンがクリックされたときの処理を登録
convertButton.addEventListener('click', () => {
    // 下のボックスにメッセージを表示する
    romajiOutput.textContent = 'ボタンが押されました！';
});