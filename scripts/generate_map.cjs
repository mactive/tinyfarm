const fs = require('fs');
const path = require('path');

const mapWidth = 24;
const mapHeight = 24;
const tileWidth = 16;
const tileHeight = 16;

const layers = [
  {
    name: "Ground",
    type: "tilelayer",
    x: 0,
    y: 0,
    width: mapWidth,
    height: mapHeight,
    visible: true,
    opacity: 1,
    data: []
  },
  {
    name: "Fences",
    type: "tilelayer",
    x: 0,
    y: 0,
    width: mapWidth,
    height: mapHeight,
    visible: true,
    opacity: 1,
    data: []
  },
  {
    name: "Objects",
    type: "tilelayer",
    x: 0,
    y: 0,
    width: mapWidth,
    height: mapHeight,
    visible: true,
    opacity: 1,
    data: []
  }
];

// Fill Ground with random grass tiles (GID 1-11 for first row of grass)
// Grass.png is 176x112 (11 cols x 7 rows)
// Let's use a mix of basic grass tiles from the first row (GID 1-3)
for (let i = 0; i < mapWidth * mapHeight; i++) {
  const randomGrass = Math.floor(Math.random() * 3) + 1; 
  layers[0].data.push(randomGrass);
  layers[1].data.push(0); // Empty by default
  layers[2].data.push(0); // Empty by default
}

// Add Fences around the border (GID 78 is first fence tile)
// Fences.png is 64x64 (4 cols x 4 rows)
// Let's use GID 78 for vertical, 79 for horizontal roughly
// Actually, let's just use GID 78 for simplicity, user can edit later
const fenceGID = 78; 
for (let y = 0; y < mapHeight; y++) {
  for (let x = 0; x < mapWidth; x++) {
    const index = y * mapWidth + x;
    if (x === 0 || x === mapWidth - 1 || y === 0 || y === mapHeight - 1) {
      layers[1].data[index] = fenceGID;
    }
  }
}

// Add a House in the middle
// House.png starts at GID 94 (112x80 -> 7x5 tiles)
// Let's place it at (8, 8)
const houseX = 8;
const houseY = 8;
const houseWidth = 7;
const houseHeight = 5;
const houseStartGID = 94;

for (let hy = 0; hy < houseHeight; hy++) {
  for (let hx = 0; hx < houseWidth; hx++) {
    const index = (houseY + hy) * mapWidth + (houseX + hx);
    // House tiles are sequential in the tileset image
    // Row 0: 94, 95, ...
    // Row 1: 94 + 7, ...
    // Actually, Tiled tileset GIDs are usually row-major.
    // House image width is 7 tiles.
    const tileGID = houseStartGID + (hy * 7) + hx;
    layers[2].data[index] = tileGID;
  }
}

const map = {
  compressionlevel: -1,
  height: mapHeight,
  infinite: false,
  layers: layers,
  nextlayerid: 4,
  nextobjectid: 1,
  orientation: "orthogonal",
  renderorder: "right-down",
  tiledversion: "1.10.2",
  tileheight: tileHeight,
  tilesets: [
    {
      columns: 11,
      firstgid: 1,
      image: "Tilesets/Grass.png",
      imageheight: 112,
      imagewidth: 176,
      margin: 0,
      name: "Grass",
      spacing: 0,
      tilecount: 77,
      tileheight: 16,
      tilewidth: 16
    },
    {
      columns: 4,
      firstgid: 78,
      image: "Tilesets/Fences.png",
      imageheight: 64,
      imagewidth: 64,
      margin: 0,
      name: "Fences",
      spacing: 0,
      tilecount: 16,
      tileheight: 16,
      tilewidth: 16
    },
    {
      columns: 7,
      firstgid: 94,
      image: "Tilesets/Wooden House.png",
      imageheight: 80,
      imagewidth: 112,
      margin: 0,
      name: "House",
      spacing: 0,
      tilecount: 35,
      tileheight: 16,
      tilewidth: 16
    }
  ],
  tilewidth: tileWidth,
  type: "map",
  version: "1.10",
  width: mapWidth
};

fs.writeFileSync(path.join(__dirname, '../public/assets/map.json'), JSON.stringify(map, null, 2));
console.log('Map generated at public/assets/map.json');
