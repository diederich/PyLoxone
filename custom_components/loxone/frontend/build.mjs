import * as esbuild from "esbuild";

const watch = process.argv.includes("--watch");

const ctx = await esbuild.context({
  entryPoints: ["src/loxone-panel.ts"],
  bundle: true,
  minify: !watch,
  format: "esm",
  outfile: "loxone-panel.js",
  target: "es2021",
});

if (watch) {
  await ctx.watch();
  console.log("Watching for changes…");
} else {
  await ctx.rebuild();
  await ctx.dispose();
  console.log("Built loxone-panel.js");
}
