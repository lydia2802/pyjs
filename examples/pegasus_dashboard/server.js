// Plain Node.js static file server for the dist/ folder produced by build.py.
// No dependencies: just http + fs from the standard library.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DIST_DIR = join(dirname(fileURLToPath(import.meta.url)), "dist");
const PORT = process.env.PORT ? Number(process.env.PORT) : 5173;

const CONTENT_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript",
  ".css": "text/css",
  ".json": "application/json",
};

function dirname(path) {
  return path.slice(0, path.lastIndexOf("/"));
}

const server = createServer(async (req, res) => {
  const urlPath = req.url === "/" ? "/index.html" : req.url;
  const filePath = join(DIST_DIR, urlPath);

  try {
    const body = await readFile(filePath);
    res.writeHead(200, { "Content-Type": CONTENT_TYPES[extname(filePath)] || "application/octet-stream" });
    res.end(body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("404 Not Found");
  }
});

server.listen(PORT, () => {
  console.log(`Pegasus dashboard served at http://localhost:${PORT}`);
  console.log(`Serving static files from ${DIST_DIR}`);
});
