import Phaser from 'phaser';

export default class FarmScene extends Phaser.Scene {
  private player!: Phaser.Physics.Arcade.Sprite;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasd!: {
    up: Phaser.Input.Keyboard.Key;
    down: Phaser.Input.Keyboard.Key;
    left: Phaser.Input.Keyboard.Key;
    right: Phaser.Input.Keyboard.Key;
  };

  constructor() {
    super('FarmScene');
  }

  preload() {
    // Load tilemap
    this.load.tilemapTiledJSON('map', 'assets/map.json');

    // Load tilesets
    this.load.image('grass', 'assets/Tilesets/Grass.png');
    this.load.image('tilled', 'assets/Tilesets/Tilled Dirt.png');
    this.load.image('house', 'assets/Tilesets/Wooden House.png');
    this.load.image('fences', 'assets/Tilesets/Fences.png');
    this.load.image('water', 'assets/Tilesets/Water.png');
    this.load.image('grass_biom', 'assets/Objects/Basic_Grass_Biom_things.png');
    this.load.image('furniture', 'assets/Objects/Basic_Furniture.png');

    // Load character
    this.load.spritesheet('player', 'assets/Characters/Basic Charakter Spritesheet.png', {
      frameWidth: 48,
      frameHeight: 48
    });
  }

  create() {
    // Create map from Tiled JSON
    const map = this.make.tilemap({ key: 'map' });

    // Add tilesets (first argument is the name in Tiled JSON, second is the key in Phaser)
    const grassTileset = map.addTilesetImage('Grass', 'grass');
    const fencesTileset = map.addTilesetImage('Fences', 'fences');
    const houseTileset = map.addTilesetImage('House', 'house');
    const waterTileset = map.addTilesetImage('Water', 'water');
    const grassBiomTileset = map.addTilesetImage('Basic_Grass_Biom_things', 'grass_biom');
    const furnitureTileset = map.addTilesetImage('Basic_Furniture', 'furniture');

    if (!grassTileset || !fencesTileset || !houseTileset || !waterTileset || !grassBiomTileset || !furnitureTileset) {
      console.error('Failed to load tilesets');
      return;
    }

    const tilesets = [grassTileset, fencesTileset, houseTileset, waterTileset, grassBiomTileset, furnitureTileset];

    // Create layers
    map.createLayer('water', tilesets, 0, 0);
    map.createLayer('Ground', tilesets, 0, 0);
    map.createLayer('tree', tilesets, 0, 0);
    const fencesLayer = map.createLayer('Fences', tilesets, 0, 0);
    map.createLayer('Objects', tilesets, 0, 0);

    // Set collisions for fences layer
    if (fencesLayer) {
      // Set collision for fence tiles (IDs: 78, 79, 80, 81 from map.json)
      // We want all fence tiles to be collidable
      fencesLayer.setCollision([78, 79, 80, 81, 101, 102, 103, 108, 110, 115, 116, 117]);
    }

    // Set world bounds to match the map size
    this.physics.world.setBounds(0, 0, map.widthInPixels, map.heightInPixels);

    // Add player at the center
    const centerX = map.widthInPixels / 2;
    const centerY = map.heightInPixels / 2;
    this.player = this.physics.add.sprite(centerX, centerY, 'player');
    this.player.setCollideWorldBounds(true);

    // Adjust collision body size and offset to match the character's feet
    // The sprite is 48x48.
    // User reported previous offset was too low.
    // Moving the collision box up to the "lower half" of the character visual area.
    this.player.setSize(16, 8);
    this.player.setOffset(16, 24);

    // Add collision between player and fences
    if (fencesLayer) {
      this.physics.add.collider(this.player, fencesLayer);
    }

    // Create animations
    // Up (Back)
    this.anims.create({
      key: 'walk-up',
      frames: this.anims.generateFrameNumbers('player', { start: 4, end: 7 }),
      frameRate: 10,
      repeat: -1
    });

    // Down (Front)
    this.anims.create({
      key: 'walk-down',
      frames: this.anims.generateFrameNumbers('player', { start: 0, end: 3 }),
      frameRate: 10,
      repeat: -1
    });

    // Left
    this.anims.create({
      key: 'walk-left',
      frames: this.anims.generateFrameNumbers('player', { start: 8, end: 11 }),
      frameRate: 10,
      repeat: -1
    });

    // Right
    this.anims.create({
      key: 'walk-right',
      frames: this.anims.generateFrameNumbers('player', { start: 12, end: 15 }),
      frameRate: 10,
      repeat: -1
    });

    // Idle animations (using the first frame of each direction)
    this.anims.create({
      key: 'idle-up',
      frames: [{ key: 'player', frame: 4 }],
      frameRate: 20
    });

    this.anims.create({
      key: 'idle-down',
      frames: [{ key: 'player', frame: 0 }],
      frameRate: 20
    });

    this.anims.create({
      key: 'idle-left',
      frames: [{ key: 'player', frame: 8 }],
      frameRate: 20
    });

    this.anims.create({
      key: 'idle-right',
      frames: [{ key: 'player', frame: 12 }],
      frameRate: 20
    });

    // Controls
    if (this.input.keyboard) {
      this.cursors = this.input.keyboard.createCursorKeys();
      this.wasd = this.input.keyboard.addKeys({
        up: Phaser.Input.Keyboard.KeyCodes.W,
        down: Phaser.Input.Keyboard.KeyCodes.S,
        left: Phaser.Input.Keyboard.KeyCodes.A,
        right: Phaser.Input.Keyboard.KeyCodes.D
      }) as any;
    }

    this.player.play('idle-down');

    // Camera
    this.cameras.main.startFollow(this.player);
    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    this.cameras.main.setZoom(2);

    // Set debug velocity scale manually since it's not in the main config type
    // This makes the velocity vector length proportional to speed. 
    // Speed 100 * 0.16 = 16px length
    if (this.physics.world && (this.physics.world as any).defaults) {
      (this.physics.world as any).defaults.debugVelocityScale = 0.16;
    }
  }

  update() {
    if (!this.cursors || !this.wasd || !this.player || !this.player.body) return;

    const speed = 100;

    this.player.setVelocity(0);

    const left = this.cursors.left.isDown || this.wasd.left.isDown;
    const right = this.cursors.right.isDown || this.wasd.right.isDown;
    const up = this.cursors.up.isDown || this.wasd.up.isDown;
    const down = this.cursors.down.isDown || this.wasd.down.isDown;

    // Movement logic
    if (left) {
      this.player.setVelocityX(-speed);
    } else if (right) {
      this.player.setVelocityX(speed);
    }

    if (up) {
      this.player.setVelocityY(-speed);
    } else if (down) {
      this.player.setVelocityY(speed);
    }

    // Normalize and scale the velocity so that player can't move faster along a diagonal
    this.player.body.velocity.normalize().scale(speed);

    // Update animations
    if (left) {
      this.player.play('walk-left', true);
    } else if (right) {
      this.player.play('walk-right', true);
    } else if (up) {
      this.player.play('walk-up', true);
    } else if (down) {
      this.player.play('walk-down', true);
    } else {
      // Idle state - determine based on previous velocity or current animation
      const currentAnim = this.player.anims.currentAnim?.key;

      if (this.player.body.velocity.x === 0 && this.player.body.velocity.y === 0) {
        // If we were moving, switch to idle based on the last movement direction
        if (currentAnim === 'walk-left') {
          this.player.play('idle-left');
        } else if (currentAnim === 'walk-right') {
          this.player.play('idle-right');
        } else if (currentAnim === 'walk-up') {
          this.player.play('idle-up');
        } else if (currentAnim === 'walk-down') {
          this.player.play('idle-down');
        }
      }
    }
  }
}
