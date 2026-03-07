import Phaser from 'phaser';

export default class FarmScene extends Phaser.Scene {
  private player!: Phaser.Physics.Arcade.Sprite;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;

  constructor() {
    super('FarmScene');
  }

  preload() {
    // Load tilesets
    this.load.image('grass', 'assets/Tilesets/Grass.png');
    this.load.image('tilled', 'assets/Tilesets/Tilled Dirt.png');
    this.load.image('house', 'assets/Tilesets/Wooden House.png');
    this.load.image('fences', 'assets/Tilesets/Fences.png');
    
    // Load character
    this.load.spritesheet('player', 'assets/Characters/Basic Charakter Spritesheet.png', {
      frameWidth: 48,
      frameHeight: 48
    });
  }

  create() {
    // Create map
    const mapWidth = 20;
    const mapHeight = 15;
    const tileSize = 16; // Assuming 16x16 tiles based on standard pixel art packs

    // Create a simple grass background
    // Since we don't have a tilemap JSON, we'll just tile the grass image
    // But 'Grass.png' is likely a tileset, not a single tile.
    // Let's assume it's a tileset.
    // For simplicity without a map editor, I'll create a blank tilemap.
    
    const map = this.make.tilemap({ width: mapWidth, height: mapHeight, tileWidth: tileSize, tileHeight: tileSize });
    
    // We need to know the structure of 'Grass.png'.
    // Usually it has multiple tiles.
    // I'll just add the tileset and fill with the first tile for now.
    const tileset = map.addTilesetImage('grass', 'grass', tileSize, tileSize);
    
    if (tileset) {
        const layer = map.createBlankLayer('Ground', tileset);
        if (layer) {
            layer.fill(0); // Fill with the first tile (index 0)
            
            // Randomly place some other grass variations if possible
            // But without seeing the tileset, index 0 is safe.
        }
    }

    // Add a house (just as an image for now if it's a single building)
    // Wooden House.png might be a tileset or a single image.
    // If it's a tileset, we need to map it.
    // Let's just add it as an image to be safe and simple.
    this.add.image(200, 150, 'house');

    // Add player
    this.player = this.physics.add.sprite(400, 300, 'player');
    this.player.setCollideWorldBounds(true);

    // Create animations
    this.anims.create({
      key: 'idle',
      frames: this.anims.generateFrameNumbers('player', { start: 0, end: 1 }),
      frameRate: 4,
      repeat: -1
    });

    this.anims.create({
      key: 'walk-down',
      frames: this.anims.generateFrameNumbers('player', { start: 0, end: 3 }),
      frameRate: 10,
      repeat: -1
    });
    
    // Basic controls
    if (this.input.keyboard) {
        this.cursors = this.input.keyboard.createCursorKeys();
    }

    this.player.play('idle');
    
    // Camera
    this.cameras.main.startFollow(this.player);
    this.cameras.main.setZoom(2);
  }

  update() {
    if (!this.cursors || !this.player || !this.player.body) return;

    const speed = 100;

    this.player.setVelocity(0);

    if (this.cursors.left.isDown) {
      this.player.setVelocityX(-speed);
      this.player.setFlipX(true);
    } else if (this.cursors.right.isDown) {
      this.player.setVelocityX(speed);
      this.player.setFlipX(false);
    }

    if (this.cursors.up.isDown) {
      this.player.setVelocityY(-speed);
    } else if (this.cursors.down.isDown) {
      this.player.setVelocityY(speed);
    }

    // Normalize and scale the velocity so that player can't move faster along a diagonal
    this.player.body.velocity.normalize().scale(speed);

    // Animations
    if (this.player.body.velocity.x !== 0 || this.player.body.velocity.y !== 0) {
      this.player.play('walk-down', true);
    } else {
      this.player.play('idle', true);
    }
  }
}
