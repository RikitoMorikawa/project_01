#!/usr/bin/env node

/**
 * フロントエンドビルド最適化スクリプト
 *
 * バンドルサイズの最適化、不要ファイルの削除、
 * 静的アセットの圧縮を行う
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
const zlib = require("zlib");

// 設定
const CONFIG = {
  outputDir: "out",
  compressionLevel: 9,
  minFileSize: 1024, // 1KB 以上のファイルを圧縮対象とする
  excludeExtensions: [".gz", ".br", ".map"],
  staticAssetExtensions: [".js", ".css", ".html", ".json", ".svg", ".ico"],
  imageExtensions: [".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"],
};

// ログ出力
const log = {
  info: (msg) => console.log(`\x1b[36m[INFO]\x1b[0m ${msg}`),
  success: (msg) => console.log(`\x1b[32m[SUCCESS]\x1b[0m ${msg}`),
  warning: (msg) => console.log(`\x1b[33m[WARNING]\x1b[0m ${msg}`),
  error: (msg) => console.log(`\x1b[31m[ERROR]\x1b[0m ${msg}`),
};

/**
 * ファイルサイズを人間が読みやすい形式に変換
 */
function formatFileSize(bytes) {
  const sizes = ["B", "KB", "MB", "GB"];
  if (bytes === 0) return "0 B";
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + " " + sizes[i];
}

/**
 * ディレクトリ内のファイルを再帰的に取得
 */
function getFilesRecursively(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      getFilesRecursively(filePath, fileList);
    } else {
      fileList.push(filePath);
    }
  });

  return fileList;
}

/**
 * バンドル分析の実行
 */
function analyzeBundles() {
  log.info("バンドル分析を実行中...");

  try {
    // webpack-bundle-analyzer を使用してバンドル分析
    execSync("ANALYZE=true npm run build", { stdio: "inherit" });
    log.success("バンドル分析が完了しました");
    log.info("分析結果: bundle-analyzer-report.html を確認してください");
  } catch (error) {
    log.warning("バンドル分析をスキップしました（webpack-bundle-analyzer が必要）");
  }
}

/**
 * 不要ファイルの削除
 */
function removeUnnecessaryFiles() {
  log.info("不要ファイルを削除中...");

  const outputPath = path.join(process.cwd(), CONFIG.outputDir);
  if (!fs.existsSync(outputPath)) {
    log.warning(`出力ディレクトリが見つかりません: ${outputPath}`);
    return;
  }

  const files = getFilesRecursively(outputPath);
  let removedCount = 0;
  let savedBytes = 0;

  files.forEach((filePath) => {
    const ext = path.extname(filePath);
    const fileName = path.basename(filePath);

    // ソースマップファイルを削除（本番環境）
    if (ext === ".map" && process.env.NODE_ENV === "production") {
      const stats = fs.statSync(filePath);
      fs.unlinkSync(filePath);
      removedCount++;
      savedBytes += stats.size;
      log.info(`削除: ${fileName} (${formatFileSize(stats.size)})`);
    }

    // 空のファイルを削除
    if (fs.statSync(filePath).size === 0) {
      fs.unlinkSync(filePath);
      removedCount++;
      log.info(`削除: ${fileName} (空ファイル)`);
    }
  });

  log.success(`不要ファイル削除完了: ${removedCount} ファイル, ${formatFileSize(savedBytes)} 節約`);
}

/**
 * Gzip 圧縮
 */
function compressWithGzip(filePath) {
  const input = fs.readFileSync(filePath);
  const compressed = zlib.gzipSync(input, { level: CONFIG.compressionLevel });
  const outputPath = `${filePath}.gz`;

  fs.writeFileSync(outputPath, compressed);

  return {
    originalSize: input.length,
    compressedSize: compressed.length,
    compressionRatio: (1 - compressed.length / input.length) * 100,
  };
}

/**
 * Brotli 圧縮
 */
function compressWithBrotli(filePath) {
  try {
    const input = fs.readFileSync(filePath);
    const compressed = zlib.brotliCompressSync(input, {
      params: {
        [zlib.constants.BROTLI_PARAM_QUALITY]: 11,
        [zlib.constants.BROTLI_PARAM_SIZE_HINT]: input.length,
      },
    });
    const outputPath = `${filePath}.br`;

    fs.writeFileSync(outputPath, compressed);

    return {
      originalSize: input.length,
      compressedSize: compressed.length,
      compressionRatio: (1 - compressed.length / input.length) * 100,
    };
  } catch (error) {
    log.warning(`Brotli 圧縮エラー: ${path.basename(filePath)}`);
    return null;
  }
}

/**
 * 静的アセットの圧縮
 */
function compressStaticAssets() {
  log.info("静的アセットを圧縮中...");

  const outputPath = path.join(process.cwd(), CONFIG.outputDir);
  if (!fs.existsSync(outputPath)) {
    log.warning(`出力ディレクトリが見つかりません: ${outputPath}`);
    return;
  }

  const files = getFilesRecursively(outputPath);
  let compressedCount = 0;
  let totalOriginalSize = 0;
  let totalGzipSize = 0;
  let totalBrotliSize = 0;

  files.forEach((filePath) => {
    const ext = path.extname(filePath);
    const fileName = path.basename(filePath);
    const stats = fs.statSync(filePath);

    // 圧縮対象ファイルかチェック
    if (CONFIG.staticAssetExtensions.includes(ext) && !CONFIG.excludeExtensions.includes(ext) && stats.size >= CONFIG.minFileSize) {
      // Gzip 圧縮
      const gzipResult = compressWithGzip(filePath);
      totalOriginalSize += gzipResult.originalSize;
      totalGzipSize += gzipResult.compressedSize;

      // Brotli 圧縮
      const brotliResult = compressWithBrotli(filePath);
      if (brotliResult) {
        totalBrotliSize += brotliResult.compressedSize;
      }

      compressedCount++;

      log.info(
        `圧縮: ${fileName} - ` +
          `Gzip: ${formatFileSize(gzipResult.compressedSize)} (${gzipResult.compressionRatio.toFixed(1)}% 削減)` +
          (brotliResult ? `, Brotli: ${formatFileSize(brotliResult.compressedSize)} (${brotliResult.compressionRatio.toFixed(1)}% 削減)` : "")
      );
    }
  });

  const gzipSavings = totalOriginalSize - totalGzipSize;
  const brotliSavings = totalOriginalSize - totalBrotliSize;

  log.success(`静的アセット圧縮完了: ${compressedCount} ファイル`);
  log.info(`Gzip: ${formatFileSize(gzipSavings)} 節約 (${((gzipSavings / totalOriginalSize) * 100).toFixed(1)}%)`);
  if (totalBrotliSize > 0) {
    log.info(`Brotli: ${formatFileSize(brotliSavings)} 節約 (${((brotliSavings / totalOriginalSize) * 100).toFixed(1)}%)`);
  }
}

/**
 * 画像最適化
 */
function optimizeImages() {
  log.info("画像最適化をチェック中...");

  const outputPath = path.join(process.cwd(), CONFIG.outputDir);
  if (!fs.existsSync(outputPath)) {
    return;
  }

  const files = getFilesRecursively(outputPath);
  const imageFiles = files.filter((filePath) => {
    const ext = path.extname(filePath);
    return CONFIG.imageExtensions.includes(ext);
  });

  if (imageFiles.length === 0) {
    log.info("最適化対象の画像ファイルが見つかりませんでした");
    return;
  }

  let totalOriginalSize = 0;
  let totalOptimizedSize = 0;

  imageFiles.forEach((filePath) => {
    const stats = fs.statSync(filePath);
    totalOriginalSize += stats.size;
    totalOptimizedSize += stats.size; // 実際の最適化は外部ツールで行う

    log.info(`画像: ${path.basename(filePath)} (${formatFileSize(stats.size)})`);
  });

  log.info(`画像ファイル: ${imageFiles.length} 件, 合計サイズ: ${formatFileSize(totalOriginalSize)}`);
  log.info("画像最適化には imagemin や sharp などの外部ツールの使用を推奨します");
}

/**
 * ビルド統計の生成
 */
function generateBuildStats() {
  log.info("ビルド統計を生成中...");

  const outputPath = path.join(process.cwd(), CONFIG.outputDir);
  if (!fs.existsSync(outputPath)) {
    return;
  }

  const files = getFilesRecursively(outputPath);
  const stats = {
    totalFiles: 0,
    totalSize: 0,
    fileTypes: {},
    largestFiles: [],
    timestamp: new Date().toISOString(),
  };

  files.forEach((filePath) => {
    const ext = path.extname(filePath) || "no-extension";
    const fileStats = fs.statSync(filePath);
    const relativePath = path.relative(outputPath, filePath);

    stats.totalFiles++;
    stats.totalSize += fileStats.size;

    if (!stats.fileTypes[ext]) {
      stats.fileTypes[ext] = { count: 0, size: 0 };
    }
    stats.fileTypes[ext].count++;
    stats.fileTypes[ext].size += fileStats.size;

    stats.largestFiles.push({
      path: relativePath,
      size: fileStats.size,
    });
  });

  // 最大ファイルサイズでソート
  stats.largestFiles.sort((a, b) => b.size - a.size);
  stats.largestFiles = stats.largestFiles.slice(0, 10); // 上位10件

  // 統計ファイルを出力
  const statsPath = path.join(outputPath, "build-stats.json");
  fs.writeFileSync(statsPath, JSON.stringify(stats, null, 2));

  log.success(`ビルド統計を生成しました: ${statsPath}`);
  log.info(`総ファイル数: ${stats.totalFiles}`);
  log.info(`総サイズ: ${formatFileSize(stats.totalSize)}`);

  // ファイルタイプ別統計を表示
  Object.entries(stats.fileTypes)
    .sort(([, a], [, b]) => b.size - a.size)
    .slice(0, 5)
    .forEach(([ext, data]) => {
      log.info(`${ext}: ${data.count} ファイル, ${formatFileSize(data.size)}`);
    });
}

/**
 * パフォーマンスヒントの表示
 */
function showPerformanceHints() {
  log.info("パフォーマンス最適化のヒント:");

  const hints = [
    "1. 動的インポートを使用してコード分割を行う",
    "2. 画像は WebP や AVIF 形式を使用する",
    "3. 不要な依存関係を削除する",
    "4. Service Worker でキャッシング戦略を実装する",
    "5. CDN を使用して静的アセットを配信する",
    "6. Critical CSS をインライン化する",
    "7. プリロードとプリフェッチを適切に使用する",
    "8. バンドルサイズを定期的に監視する",
  ];

  hints.forEach((hint) => {
    console.log(`   ${hint}`);
  });
}

/**
 * メイン実行関数
 */
function main() {
  const startTime = Date.now();

  log.info("フロントエンドビルド最適化を開始します");

  try {
    // コマンドライン引数の解析
    const args = process.argv.slice(2);
    const shouldAnalyze = args.includes("--analyze");
    const skipCompression = args.includes("--skip-compression");

    // バンドル分析（オプション）
    if (shouldAnalyze) {
      analyzeBundles();
    }

    // 不要ファイルの削除
    removeUnnecessaryFiles();

    // 静的アセットの圧縮
    if (!skipCompression) {
      compressStaticAssets();
    }

    // 画像最適化のチェック
    optimizeImages();

    // ビルド統計の生成
    generateBuildStats();

    // パフォーマンスヒントの表示
    showPerformanceHints();

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;

    log.success(`最適化完了 (${duration.toFixed(2)}秒)`);
  } catch (error) {
    log.error(`最適化エラー: ${error.message}`);
    process.exit(1);
  }
}

// スクリプトが直接実行された場合
if (require.main === module) {
  main();
}

module.exports = {
  main,
  compressStaticAssets,
  removeUnnecessaryFiles,
  generateBuildStats,
};
