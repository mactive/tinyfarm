import Phaser from 'phaser';
import FarmScene from './scenes/FarmScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  parent: 'game-container',
  pixelArt: true, // Important for pixel art games
  zoom: 2, // Zoom in for pixel art
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { x: 0, y: 0 }, // Top-down, no gravity
      debug: false
    }
  },
  scene: [FarmScene]
};

new Phaser.Game(config);
