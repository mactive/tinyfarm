使用phaser3.9 的引擎, 一个 topdown 的2D农场游戏, 开发语言 typescript 
使用 https://cupnooble.itch.io/sprout-lands-asset-pack 的素材包 ,
我已经下载到了 `Sprout Lands - Sprites - Basic pack` 目录下.
按照 spec/land_1.png 的地图布局, 渲染出一个农场的场景
然后放置 Basic Charakter 角色 在地图上

## 已完成功能
- 地图加载与渲染
  - 使用 Tiled 导出的 `map.json`
  - 渲染图层: Ground, water, tree, Fences, Objects
  - 修复了 water 和 tree 图层未显示的 bug
- 角色控制
  - WASD / 方向键移动
  - 角色动画 (idle, walk)
  - 碰撞检测优化:
    - 缩小碰撞体积 (24x16) 并调整偏移量 (12, 24) 以贴合角色脚部
    - 解决了"隔空碰撞"和碰撞框位置偏低的问题
- 物理与调试
  - Fences 图层精确碰撞 (仅 ID 78-81 的栅栏产生碰撞)
  - 开启 Arcade Physics 调试模式 (显示碰撞框、速度向量)
  - 自定义调试样式:
    - 碰撞框: 红色
    - 静态物体: 蓝色
    - 速度向量: 黄色 (比例 0.16, 长度随速度变化)
- 视觉优化
  - 设置背景色为 `#9bd4c3` (取自水面颜色) 以减少加载时的突兀感
- 工程配置
  - 添加 `.npmrc` 指定官方源 `https://registry.npmjs.org/`