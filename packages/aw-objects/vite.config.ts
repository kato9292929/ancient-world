import { defineConfig } from "vite";

// 相対パスで出力。別プロジェクトとしてどのパスに置いても動くように。
export default defineConfig({
  base: "./",
  build: {
    outDir: "dist",
    target: "es2022",
  },
});
