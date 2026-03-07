import Phaser from 'phaser';
import FarmScene from './scenes/FarmScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  parent: 'game-container',
  pixelArt: true, // Important for pixel art games
  zoom: 2, // Zoom in for pixel art
  backgroundColor: '#9bd4c3', // Water color from Tilesets/Water.png
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { x: 0, y: 0 }, // Top-down, no gravity
      debug: true,
      debugShowBody: true,
      debugShowStaticBody: true,
      debugShowVelocity: false,
      debugVelocityColor: 0xffff00, // Yellow arrow for movement direction
      debugBodyColor: 0xffee00, // yellow box for collision area
      debugStaticBodyColor: 0x0000ff // Blue box for static objects
    }
  },
  scene: [FarmScene]
};

new Phaser.Game(config);
