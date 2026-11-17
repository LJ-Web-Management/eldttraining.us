// Regenerates generator/data/us_map.json (state outlines for the clickable map).
// Source: us-atlas states-albers-10m (U.S. Census Bureau cartographic boundaries,
// pre-projected with d3.geoAlbersUsa into a 975x610 box).
//
//   mkdir /tmp/mapdeps && cd /tmp/mapdeps && npm i us-atlas@3.0.1 topojson-client@3.1.0 topojson-simplify@3.0.3 d3-geo@3.1.1
//   node generator/tools/make_us_map.cjs /tmp/mapdeps [minWeight]
const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

const deps = createRequire(path.join(path.resolve(process.argv[2] || "."), "noop.js"));
const topojson = deps("topojson-client");
const simplify = deps("topojson-simplify");
const d3 = deps("d3-geo");
const minWeight = Number(process.argv[3] || 1.2);

const topo = JSON.parse(fs.readFileSync(deps.resolve("us-atlas/states-albers-10m.json"), "utf8"));
const simple = simplify.simplify(simplify.presimplify(topo), minWeight);
const states = topojson.feature(simple, simple.objects.states).features;
const geo = d3.geoPath(null).digits(1);

const out = states.map((f) => {
  // label at the centroid of the largest polygon (e.g. Michigan's lower peninsula)
  let best = f.geometry;
  if (f.geometry.type === "MultiPolygon") {
    let max = -1;
    for (const coords of f.geometry.coordinates) {
      const poly = { type: "Polygon", coordinates: coords };
      const a = geo.area(poly);
      if (a > max) { max = a; best = poly; }
    }
  }
  const [cx, cy] = geo.centroid(best);
  return { name: f.properties.name, d: geo(f), cx: +cx.toFixed(1), cy: +cy.toFixed(1), area: Math.round(geo.area(f)) };
});
out.sort((a, b) => a.name.localeCompare(b.name));
const dest = path.join(__dirname, "..", "data", "us_map.json");
fs.writeFileSync(dest, JSON.stringify(out));
console.log(`${out.length} states, ${fs.statSync(dest).size} bytes -> ${dest}`);
