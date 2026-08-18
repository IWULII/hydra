# Infinitode TD - Tower Defense Game

A tower defense game inspired by Infinitode, featuring endless survival gameplay with geometric neon visuals.

## Features

### Core Gameplay
- **Endless Survival Mode**: Enemies spawn infinitely with exponential difficulty scaling
- **20+ Tower Types**: Basic, Blast, Freeze, Flame, Tesla, Air, and Miner towers
- **Tower Synergies**: Combine freeze towers to slow enemies with blast/tesla towers for maximum damage
- **Smart Targeting**: Towers automatically target enemies closest to the base
- **Upgrade System**: Upgrade towers up to level 10 with increasing stats

### Economy & Strategy
- **Resource Miners**: Build miners on empty cells to generate passive income
- **Maze Building**: Create optimal paths by strategically placing towers
- **Wave Management**: Start waves manually when ready

### Meta-Game
- **Research Tree**: Spend research points on permanent upgrades between games
- **Statistics Tracking**: Track waves survived, enemies killed, and more
- **Multiple Difficulties**: Choose your challenge level

### Visual Style
- **Neon Geometric Design**: Clean, readable visuals inspired by Infinitode
- **Particle Effects**: Satisfying explosion and impact effects
- **Status Indicators**: Visual feedback for frozen and burning enemies

## Controls

- **Left Click**: Place selected tower / Select tower
- **Right Click**: Cancel tower selection
- **Space**: Start next wave
- **R**: Open Research menu
- **ESC**: Pause/Resume game

## Installation

### Run from Source
```bash
pip install pygame numpy
python main.py
```

### Build Windows Executable
```bash
pip install pyinstaller
python build.py
```

The executable will be created at `dist/InfinitodeTD.exe`

## Requirements

- Python 3.8+
- pygame
- numpy
- pyinstaller (for building .exe)

## Configuration

The game supports variable screen resolutions:
- Default: 1920x1080
- Minimum: 1024x768
- Fullscreen mode supported

Settings are saved in `config/settings.json`

## Tower Types

| Tower | Cost | Special Ability |
|-------|------|----------------|
| Basic | 50g | Balanced damage and range |
| Blast | 100g | Area damage splash |
| Freeze | 80g | Slows enemies by 50% |
| Flame | 90g | Rapid fire, burns enemies |
| Tesla | 120g | Chains to multiple targets |
| Air | 100g | Bonus vs fast enemies |
| Miner | 75g | Generates passive gold |

## Enemy Types

- **Basic**: Standard enemy, balanced stats
- **Fast**: High speed, low health
- **Tank**: High health, armor, slow speed
- **Boss**: Appears every 10 waves, massive health pool

## Tips

1. **Early Game**: Start with Basic towers and a few Miners for economy
2. **Mid Game**: Add Freeze towers to control enemy flow
3. **Late Game**: Use Blast and Tesla towers for area damage
4. **Positioning**: Place towers along the longest possible path
5. **Upgrades**: Focus on upgrading key towers rather than spreading resources thin

## License

This is a fan-made project inspired by Infinitode. All rights to the original game belong to its creators.
