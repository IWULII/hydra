#!/usr/bin/env python3
"""
Infinitode-style Tower Defense Game
Main entry point
"""

import pygame
import sys
import json
import os
import random
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

# Initialize Pygame
pygame.init()
try:
    pygame.mixer.init()
except:
    # Audio not available (e.g., on server)
    pass

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
MIN_WIDTH = 1024
MIN_HEIGHT = 768
FPS = 60
TILE_SIZE = 40
GRID_WIDTH = 40
GRID_HEIGHT = 25

# Colors (Neon geometric style like Infinitode)
COLORS = {
    'background': (10, 10, 20),
    'grid': (30, 30, 50),
    'path': (25, 25, 40),
    'base': (0, 255, 128),
    'enemy_basic': (255, 50, 50),
    'enemy_fast': (255, 150, 50),
    'enemy_tank': (200, 50, 200),
    'enemy_boss': (255, 0, 255),
    'tower_basic': (50, 150, 255),
    'tower_blast': (255, 100, 50),
    'tower_freeze': (50, 200, 255),
    'tower_flame': (255, 100, 50),
    'tower_tesla': (255, 255, 100),
    'tower_air': (150, 100, 255),
    'tower_miner': (100, 255, 100),
    'projectile_basic': (100, 200, 255),
    'projectile_blast': (255, 150, 50),
    'projectile_freeze': (100, 255, 255),
    'projectile_flame': (255, 100, 0),
    'projectile_tesla': (255, 255, 150),
    'ui_bg': (20, 20, 40, 200),
    'ui_border': (100, 100, 200),
    'text_primary': (255, 255, 255),
    'text_secondary': (150, 150, 200),
    'gold': (255, 215, 0),
    'red': (255, 50, 50),
    'green': (50, 255, 100),
}

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5
    RESEARCH = 6

class TowerType(Enum):
    BASIC = "basic"
    BLAST = "blast"
    FREEZE = "freeze"
    FLAME = "flame"
    TESLA = "tesla"
    AIR = "air"
    MINER = "miner"

class EnemyType(Enum):
    BASIC = "basic"
    FAST = "fast"
    TANK = "tank"
    BOSS = "boss"

@dataclass
class TowerStats:
    damage: float = 10
    range: float = 150
    attack_speed: float = 1.0
    cost: int = 50
    color: Tuple[int, int, int] = COLORS['tower_basic']
    projectile_speed: float = 300
    special_effect: str = ""
    splash_radius: float = 0
    slow_factor: float = 1.0
    chain_count: int = 0

@dataclass
class EnemyStats:
    health: float = 100
    speed: float = 50
    reward: int = 10
    color: Tuple[int, int, int] = COLORS['enemy_basic']
    size: float = 15
    armor: float = 0

@dataclass
class ResearchNode:
    id: str
    name: str
    description: str
    cost: int
    effect_type: str
    effect_value: float
    unlocked: bool = False
    purchased: bool = False
    prerequisites: List[str] = field(default_factory=list)

class GameConfig:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.fullscreen = False
        self.difficulty = 1.0
        self.load_config()
    
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = json.load(f)
                self.screen_width = data.get('width', SCREEN_WIDTH)
                self.screen_height = data.get('height', SCREEN_HEIGHT)
                self.fullscreen = data.get('fullscreen', False)
    
    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump({
                'width': self.screen_width,
                'height': self.screen_height,
                'fullscreen': self.fullscreen
            }, f, indent=2)

class Tower:
    def __init__(self, x: int, y: int, tower_type: TowerType, level: int = 1):
        self.grid_x = x
        self.grid_y = y
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.tower_type = tower_type
        self.level = level
        self.angle = 0
        self.target_enemy = None
        self.attack_cooldown = 0
        self.stats = self.get_base_stats()
        self.upgrade_cost = int(self.stats.cost * 1.5)
        
    def get_base_stats(self) -> TowerStats:
        stats = {
            TowerType.BASIC: TowerStats(
                damage=15, range=150, attack_speed=1.5, cost=50,
                color=COLORS['tower_basic'], projectile_speed=400
            ),
            TowerType.BLAST: TowerStats(
                damage=25, range=120, attack_speed=0.8, cost=100,
                color=COLORS['tower_blast'], projectile_speed=300,
                splash_radius=80
            ),
            TowerType.FREEZE: TowerStats(
                damage=8, range=130, attack_speed=1.2, cost=80,
                color=COLORS['tower_freeze'], projectile_speed=350,
                slow_factor=0.5
            ),
            TowerType.FLAME: TowerStats(
                damage=5, range=100, attack_speed=3.0, cost=90,
                color=COLORS['tower_flame'], projectile_speed=200
            ),
            TowerType.TESLA: TowerStats(
                damage=20, range=140, attack_speed=1.0, cost=120,
                color=COLORS['tower_tesla'], projectile_speed=500,
                chain_count=3
            ),
            TowerType.AIR: TowerStats(
                damage=30, range=180, attack_speed=1.0, cost=100,
                color=COLORS['tower_air'], projectile_speed=600
            ),
            TowerType.MINER: TowerStats(
                damage=0, range=0, attack_speed=0.5, cost=75,
                color=COLORS['tower_miner']
            ),
        }
        base = stats[self.tower_type]
        # Apply level bonuses
        multiplier = 1 + (self.level - 1) * 0.15
        return TowerStats(
            damage=base.damage * multiplier,
            range=base.range * (1 + (self.level - 1) * 0.05),
            attack_speed=base.attack_speed * (1 + (self.level - 1) * 0.1),
            cost=base.cost,
            color=base.color,
            projectile_speed=base.projectile_speed,
            special_effect=base.special_effect,
            splash_radius=base.splash_radius,
            slow_factor=base.slow_factor,
            chain_count=base.chain_count
        )
    
    def upgrade(self) -> bool:
        if self.level >= 10:
            return False
        self.level += 1
        self.stats = self.get_base_stats()
        self.upgrade_cost = int(self.stats.cost * 1.5 * self.level)
        return True
    
    def draw(self, screen: pygame.Surface):
        rect = pygame.Rect(
            self.grid_x * TILE_SIZE + 2,
            self.grid_y * TILE_SIZE + 2,
            TILE_SIZE - 4,
            TILE_SIZE - 4
        )
        pygame.draw.rect(screen, self.stats.color, rect, border_radius=8)
        
        # Level indicator
        for i in range(min(self.level, 5)):
            dot_x = self.x - 10 + i * 5
            dot_y = self.y + TILE_SIZE // 2 - 5
            pygame.draw.circle(screen, COLORS['gold'], (int(dot_x), int(dot_y)), 3)
        
        # Range circle when selected
        if hasattr(self, 'selected') and self.selected:
            range_surf = pygame.Surface((int(self.stats.range * 2), int(self.stats.range * 2)), pygame.SRCALPHA)
            pygame.draw.circle(range_surf, (*self.stats.color, 50), 
                             (int(self.stats.range), int(self.stats.range)), 
                             int(self.stats.range), 2)
            screen.blit(range_surf, (self.x - self.stats.range, self.y - self.stats.range))

class Enemy:
    def __init__(self, enemy_type: EnemyType, wave: int, path: List[Tuple[int, int]]):
        self.enemy_type = enemy_type
        self.path = path
        self.current_waypoint = 0
        self.x, self.y = path[0]
        self.health = 0
        self.max_health = 0
        self.speed = 0
        self.reward = 0
        self.frozen = False
        self.freeze_timer = 0
        self.burning = False
        self.burn_timer = 0
        self.burn_damage = 0
        self.set_stats(wave)
        
    def set_stats(self, wave: int):
        base_stats = {
            EnemyType.BASIC: EnemyStats(
                health=100, speed=60, reward=10,
                color=COLORS['enemy_basic'], size=15
            ),
            EnemyType.FAST: EnemyStats(
                health=60, speed=100, reward=15,
                color=COLORS['enemy_fast'], size=12
            ),
            EnemyType.TANK: EnemyStats(
                health=300, speed=30, reward=25,
                color=COLORS['enemy_tank'], size=20, armor=5
            ),
            EnemyType.BOSS: EnemyStats(
                health=1000, speed=20, reward=100,
                color=COLORS['enemy_boss'], size=30, armor=10
            ),
        }
        
        base = base_stats[self.enemy_type]
        # Exponential scaling
        scale = 1.15 ** (wave - 1)
        
        self.max_health = base.health * scale
        self.health = self.max_health
        self.speed = base.speed
        self.reward = int(base.reward * scale)
        self.color = base.color
        self.size = base.size
        self.armor = base.armor
    
    def update(self, dt: float, game_difficulty: float = 1.0):
        if self.frozen:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.frozen = False
            actual_speed = self.speed * 0.5 * dt
        else:
            actual_speed = self.speed * dt
        
        if self.burning:
            self.burn_timer -= dt
            self.health -= self.burn_damage * dt
            if self.burn_timer <= 0:
                self.burning = False
        
        if self.current_waypoint < len(self.path) - 1:
            target_x, target_y = self.path[self.current_waypoint + 1]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist > 0:
                self.x += (dx / dist) * actual_speed
                self.y += (dy / dist) * actual_speed
                
                if dist < 5:
                    self.current_waypoint += 1
    
    def take_damage(self, damage: float, slow_factor: float = 1.0, 
                   apply_slow: bool = False, apply_burn: bool = False):
        actual_damage = max(1, damage - self.armor)
        self.health -= actual_damage
        
        if apply_slow and slow_factor < 1.0:
            self.frozen = True
            self.freeze_timer = 2.0
        
        if apply_burn:
            self.burning = True
            self.burn_timer = 3.0
            self.burn_damage = damage * 0.1
    
    def draw(self, screen: pygame.Surface):
        # Draw enemy
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))
        
        # Health bar
        bar_width = self.size * 2
        bar_height = 4
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.size - 8
        
        pygame.draw.rect(screen, COLORS['red'], 
                        (bar_x, bar_y, bar_width, bar_height))
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0
        pygame.draw.rect(screen, COLORS['green'],
                        (bar_x, bar_y, bar_width * health_ratio, bar_height))
        
        # Status effects
        if self.frozen:
            pygame.draw.circle(screen, COLORS['tower_freeze'], 
                             (int(self.x), int(self.y)), int(self.size), 2)
        if self.burning:
            pygame.draw.circle(screen, COLORS['tower_flame'],
                             (int(self.x), int(self.y)), int(self.size) - 3, 2)

class Projectile:
    def __init__(self, start_x: float, start_y: float, target: Enemy, 
                 tower: Tower, damage: float):
        self.x = start_x
        self.y = start_y
        self.target = target
        self.tower = tower
        self.damage = damage
        self.speed = tower.stats.projectile_speed
        self.active = True
        self.hit = False
        
    def update(self, dt: float):
        if not self.target or self.target.health <= 0:
            self.active = False
            return
        
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < self.speed * dt:
            self.hit = True
            self.active = False
            
            # Apply effects
            apply_slow = self.tower.tower_type == TowerType.FREEZE
            apply_burn = self.tower.tower_type == TowerType.FLAME
            slow_factor = self.tower.stats.slow_factor if apply_slow else 1.0
            
            self.target.take_damage(self.damage, slow_factor, apply_slow, apply_burn)
            
            # Splash damage
            if self.tower.stats.splash_radius > 0:
                # Handle splash in game loop
                pass
        else:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
    
    def draw(self, screen: pygame.Surface):
        color = {
            TowerType.BASIC: COLORS['projectile_basic'],
            TowerType.BLAST: COLORS['projectile_blast'],
            TowerType.FREEZE: COLORS['projectile_freeze'],
            TowerType.FLAME: COLORS['projectile_flame'],
            TowerType.TESLA: COLORS['projectile_tesla'],
            TowerType.AIR: COLORS['projectile_basic'],
        }.get(self.tower.tower_type, COLORS['projectile_basic'])
        
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 4)

class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], 
                 velocity: Tuple[float, float], lifetime: float):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.active = True
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
    
    def draw(self, screen: pygame.Surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color[:3], alpha) if len(self.color) == 3 else self.color
        size = int(3 * (self.lifetime / self.max_lifetime))
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class ResourceManager:
    def __init__(self):
        self.gold = 250
        self.lives = 20
        self.wave = 1
        self.enemies_spawned = 0
        self.enemies_killed = 0
        self.total_damage_dealt = 0
        self.towers_placed = 0
        
    def add_gold(self, amount: int):
        self.gold += amount
    
    def spend_gold(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
    
    def lose_life(self, amount: int = 1):
        self.lives -= amount
    
    def next_wave(self):
        self.wave += 1
        self.enemies_spawned = 0

class ResearchManager:
    def __init__(self):
        self.research_points = 0
        self.nodes: Dict[str, ResearchNode] = {}
        self.load_researches()
    
    def load_researches(self):
        # Define research tree
        self.nodes = {
            'damage_1': ResearchNode(
                'damage_1', 'Basic Damage I', '+10% Basic Tower Damage',
                100, 'damage', 0.1, unlocked=True
            ),
            'damage_2': ResearchNode(
                'damage_2', 'Basic Damage II', '+20% Basic Tower Damage',
                250, 'damage', 0.2, prerequisites=['damage_1']
            ),
            'attack_speed_1': ResearchNode(
                'attack_speed_1', 'Attack Speed I', '+10% Attack Speed',
                150, 'attack_speed', 0.1, unlocked=True
            ),
            'range_1': ResearchNode(
                'range_1', 'Extended Range', '+15% Tower Range',
                200, 'range', 0.15, prerequisites=['attack_speed_1']
            ),
            'economy_1': ResearchNode(
                'economy_1', 'Efficient Mining', '+20% Miner Income',
                100, 'economy', 0.2, unlocked=True
            ),
            'freeze_power': ResearchNode(
                'freeze_power', 'Deep Freeze', 'Freeze lasts 50% longer',
                300, 'freeze_duration', 0.5, prerequisites=['range_1']
            ),
            'crit_chance': ResearchNode(
                'crit_chance', 'Critical Hits', '5% chance for 2x damage',
                500, 'crit_chance', 0.05, prerequisites=['damage_2']
            ),
        }
    
    def purchase(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node and node.unlocked and not node.purchased:
            if self.research_points >= node.cost:
                self.research_points -= node.cost
                node.purchased = True
                return True
        return False
    
    def can_unlock(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node and not node.unlocked:
            for prereq in node.prerequisites:
                if not self.nodes[prereq].purchased:
                    return False
            return True
        return False

class MapGenerator:
    @staticmethod
    def generate_maze(width: int, height: int) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
        """Generate a maze-like path on the grid"""
        grid = [[0 for _ in range(width)] for _ in range(height)]
        
        # Create a winding path from left to right
        path = []
        current_y = height // 2
        
        # Start from left edge
        start_x = 0
        path.append((start_x * TILE_SIZE + TILE_SIZE // 2, 
                    current_y * TILE_SIZE + TILE_SIZE // 2))
        
        x = 1
        while x < width - 1:
            # Add some variation
            if random.random() < 0.3 and x > 2:
                # Go up or down
                direction = random.choice([-1, 1])
                for _ in range(random.randint(1, 3)):
                    new_y = current_y + direction
                    if 2 <= new_y < height - 2:
                        current_y = new_y
                        path.append((x * TILE_SIZE + TILE_SIZE // 2,
                                   current_y * TILE_SIZE + TILE_SIZE // 2))
                        grid[current_y][x] = 1
            
            path.append((x * TILE_SIZE + TILE_SIZE // 2,
                        current_y * TILE_SIZE + TILE_SIZE // 2))
            grid[current_y][x] = 1
            x += 1
        
        # End at right edge
        path.append(((width - 1) * TILE_SIZE + TILE_SIZE // 2,
                    current_y * TILE_SIZE + TILE_SIZE // 2))
        grid[current_y][width - 1] = 1
        
        return grid, path

class Game:
    def __init__(self):
        self.config = GameConfig()
        self.flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        if self.config.fullscreen:
            self.flags |= pygame.FULLSCREEN
        
        self.screen = pygame.display.set_mode(
            (self.config.screen_width, self.config.screen_height), 
            self.flags, vsync=1
        )
        pygame.display.set_caption("Infinitode TD")
        
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.state = GameState.MENU
        self.running = True
        
        # Game objects
        self.resource_manager = ResourceManager()
        self.research_manager = ResearchManager()
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.particles: List[Particle] = []
        self.grid: List[List[int]] = []
        self.path: List[Tuple[int, int]] = []
        
        self.spawn_timer = 0
        self.spawn_interval = 2.0
        self.selected_tower_type = None
        self.selected_tower = None
        self.game_difficulty = 1.0
        
        self.stats = {
            'total_waves': 0,
            'enemies_killed': 0,
            'towers_placed': 0,
            'damage_dealt': 0,
            'gold_earned': 0,
        }
        
    def new_game(self):
        self.resource_manager = ResourceManager()
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.particles = []
        self.grid, self.path = MapGenerator.generate_maze(GRID_WIDTH, GRID_HEIGHT)
        self.spawn_timer = 0
        self.selected_tower_type = None
        self.selected_tower = None
        self.state = GameState.PLAYING
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.MENU:
                        self.running = False
                
                if self.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.start_next_wave()
                    if event.key == pygame.K_r:
                        self.state = GameState.RESEARCH
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.handle_mouse_click(mouse_pos, event.button)
    
    def handle_mouse_click(self, pos: Tuple[int, int], button: int):
        if self.state != GameState.PLAYING:
            return
        
        grid_x = pos[0] // TILE_SIZE
        grid_y = pos[1] // TILE_SIZE
        
        if button == 1:  # Left click
            # Check UI clicks first
            if self.check_ui_click(pos):
                return
            
            # Try to place tower
            if self.selected_tower_type:
                self.try_place_tower(grid_x, grid_y)
            else:
                # Select existing tower
                self.select_tower_at(grid_x, grid_y)
        
        elif button == 3:  # Right click
            self.selected_tower_type = None
            self.selected_tower = None
    
    def check_ui_click(self, pos: Tuple[int, int]) -> bool:
        # Check tower selection buttons
        ui_start_x = self.config.screen_width - 200
        if pos[0] >= ui_start_x:
            button_y = 100
            for tower_type in TowerType:
                if button_y <= pos[1] <= button_y + 50:
                    if tower_type != TowerType.MINER or True:  # Allow miners
                        self.selected_tower_type = tower_type
                        self.selected_tower = None
                        return True
                button_y += 60
            
            # Check upgrade button
            if self.selected_tower:
                if 100 <= pos[1] <= 150:
                    self.upgrade_selected_tower()
                    return True
            
            return True
        return False
    
    def try_place_tower(self, grid_x: int, grid_y: int):
        if not (0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT):
            return
        
        if self.grid[grid_y][grid_x] != 0:
            return  # Cell occupied
        
        if not self.selected_tower_type:
            return
        
        tower_cost = self.get_tower_cost(self.selected_tower_type)
        if not self.resource_manager.spend_gold(tower_cost):
            return
        
        tower = Tower(grid_x, grid_y, self.selected_tower_type)
        self.towers.append(tower)
        self.grid[grid_y][grid_x] = 1
        self.resource_manager.towers_placed += 1
        self.stats['towers_placed'] += 1
        
        if self.selected_tower_type != TowerType.MINER:
            self.selected_tower_type = None
    
    def get_tower_cost(self, tower_type: TowerType) -> int:
        costs = {
            TowerType.BASIC: 50,
            TowerType.BLAST: 100,
            TowerType.FREEZE: 80,
            TowerType.FLAME: 90,
            TowerType.TESLA: 120,
            TowerType.AIR: 100,
            TowerType.MINER: 75,
        }
        return costs.get(tower_type, 50)
    
    def select_tower_at(self, grid_x: int, grid_y: int):
        for tower in self.towers:
            if tower.grid_x == grid_x and tower.grid_y == grid_y:
                self.selected_tower = tower
                self.selected_tower_type = None
                return
        self.selected_tower = None
    
    def upgrade_selected_tower(self):
        if self.selected_tower:
            if self.resource_manager.spend_gold(self.selected_tower.upgrade_cost):
                self.selected_tower.upgrade()
    
    def start_next_wave(self):
        self.resource_manager.next_wave()
        self.spawn_timer = 0
    
    def spawn_enemy(self, dt: float):
        self.spawn_timer += dt
        
        enemies_per_wave = 5 + self.resource_manager.wave * 2
        if self.resource_manager.enemies_spawned >= enemies_per_wave:
            return
        
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            
            # Determine enemy type based on wave
            rand = random.random()
            if self.resource_manager.wave % 10 == 0 and rand < 0.1:
                enemy_type = EnemyType.BOSS
            elif rand < 0.2:
                enemy_type = EnemyType.FAST
            elif rand < 0.3:
                enemy_type = EnemyType.TANK
            else:
                enemy_type = EnemyType.BASIC
            
            enemy = Enemy(enemy_type, self.resource_manager.wave, self.path)
            self.enemies.append(enemy)
            self.resource_manager.enemies_spawned += 1
    
    def update(self, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Spawn enemies
        self.spawn_enemy(dt)
        
        # Update towers
        for tower in self.towers:
            self.update_tower(tower, dt)
        
        # Update projectiles
        for proj in self.projectiles[:]:
            proj.update(dt)
            if not proj.active:
                self.projectiles.remove(proj)
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(dt, self.game_difficulty)
            
            if enemy.health <= 0:
                self.enemies.remove(enemy)
                self.resource_manager.add_gold(enemy.reward)
                self.stats['enemies_killed'] += 1
                self.stats['gold_earned'] += enemy.reward
                
                # Spawn particles
                for _ in range(5):
                    vx = random.uniform(-50, 50)
                    vy = random.uniform(-50, 50)
                    particle = Particle(enemy.x, enemy.y, enemy.color, 
                                      (vx, vy), 0.5)
                    self.particles.append(particle)
            
            # Check if enemy reached base
            if enemy.current_waypoint >= len(enemy.path) - 1:
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                    self.resource_manager.lose_life()
                    
                    if self.resource_manager.lives <= 0:
                        self.state = GameState.GAME_OVER
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.active:
                self.particles.remove(particle)
        
        # Update miners
        self.update_miners(dt)
        
        # Check game over
        if self.resource_manager.lives <= 0:
            self.state = GameState.GAME_OVER
    
    def update_tower(self, tower: Tower, dt: float):
        if tower.tower_type == TowerType.MINER:
            return  # Miners don't attack
        
        tower.attack_cooldown -= dt
        
        if tower.attack_cooldown <= 0:
            # Find target
            target = self.find_target(tower)
            if target:
                tower.target_enemy = target
                tower.angle = math.atan2(
                    target.y - tower.y,
                    target.x - tower.x
                )
                
                # Fire projectile
                proj = Projectile(tower.x, tower.y, target, tower, tower.stats.damage)
                self.projectiles.append(proj)
                tower.attack_cooldown = 1.0 / tower.stats.attack_speed
    
    def find_target(self, tower: Tower) -> Optional[Enemy]:
        valid_targets = []
        
        for enemy in self.enemies:
            dx = enemy.x - tower.x
            dy = enemy.y - tower.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist <= tower.stats.range:
                # Check if air tower can only target certain enemies
                if tower.tower_type == TowerType.AIR:
                    if enemy.enemy_type == EnemyType.FAST:
                        valid_targets.append((enemy, dist))
                else:
                    valid_targets.append((enemy, dist))
        
        if not valid_targets:
            return None
        
        # Prioritize by closest to base
        valid_targets.sort(key=lambda x: x[0].current_waypoint, reverse=True)
        return valid_targets[0][0]
    
    def update_miners(self, dt: float):
        for tower in self.towers:
            if tower.tower_type == TowerType.MINER:
                # Apply research bonuses
                bonus = 1.0
                if self.research_manager.nodes.get('economy_1', 
                          ResearchNode('', '', '', 0, '', 0)).purchased:
                    bonus = 1.2
                
                miner_income = 5 * bonus
                if random.random() < dt * tower.stats.attack_speed:
                    self.resource_manager.add_gold(int(miner_income))
    
    def draw(self):
        self.screen.fill(COLORS['background'])
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            self.draw_game()
            if self.state == GameState.PAUSED:
                self.draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        elif self.state == GameState.RESEARCH:
            self.draw_research()
        
        pygame.display.flip()
    
    def draw_menu(self):
        title = self.font_large.render("INFINITODE TD", True, COLORS['text_primary'])
        title_rect = title.get_rect(center=(self.config.screen_width // 2, 200))
        self.screen.blit(title, title_rect)
        
        # Menu options
        options = [
            "Press ENTER to Start",
            "Difficulty: Normal",
            "Press R for Research",
            "Press ESC to Quit"
        ]
        
        for i, option in enumerate(options):
            text = self.font_medium.render(option, True, COLORS['text_secondary'])
            rect = text.get_rect(center=(self.config.screen_width // 2, 350 + i * 50))
            self.screen.blit(text, rect)
    
    def draw_game(self):
        # Draw grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, 
                                 TILE_SIZE, TILE_SIZE)
                
                if self.grid[y][x] == 1:
                    pygame.draw.rect(self.screen, COLORS['path'], rect)
                else:
                    pygame.draw.rect(self.screen, COLORS['grid'], rect, 1)
        
        # Draw path
        if len(self.path) > 1:
            path_points = [(p[0], p[1]) for p in self.path]
            pygame.draw.lines(self.screen, COLORS['path'], False, 
                            path_points, TILE_SIZE // 2)
        
        # Draw base
        if self.path:
            base_x, base_y = self.path[-1]
            base_rect = pygame.Rect(base_x - 20, base_y - 20, 40, 40)
            pygame.draw.rect(self.screen, COLORS['base'], base_rect, border_radius=10)
        
        # Draw towers
        for tower in self.towers:
            tower.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(self.screen)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        # Draw tower selection
        if self.selected_tower_type:
            self.draw_placement_preview()
    
    def draw_ui(self):
        # Resource bar
        ui_bg = pygame.Surface((self.config.screen_width, 60), pygame.SRCALPHA)
        ui_bg.fill(COLORS['ui_bg'])
        self.screen.blit(ui_bg, (0, 0))
        
        # Resources
        gold_text = self.font_medium.render(f"Gold: {self.resource_manager.gold}", 
                                           True, COLORS['gold'])
        self.screen.blit(gold_text, (20, 15))
        
        lives_text = self.font_medium.render(f"Lives: {self.resource_manager.lives}",
                                            True, COLORS['red'])
        self.screen.blit(lives_text, (200, 15))
        
        wave_text = self.font_medium.render(f"Wave: {self.resource_manager.wave}",
                                           True, COLORS['text_primary'])
        self.screen.blit(wave_text, (400, 15))
        
        # Tower selection panel
        ui_panel_x = self.config.screen_width - 200
        ui_bg_panel = pygame.Surface((200, self.config.screen_height - 100), 
                                    pygame.SRCALPHA)
        ui_bg_panel.fill(COLORS['ui_bg'])
        self.screen.blit(ui_bg_panel, (ui_panel_x, 100))
        
        # Tower buttons
        tower_types = [
            (TowerType.BASIC, "Basic", 50),
            (TowerType.BLAST, "Blast", 100),
            (TowerType.FREEZE, "Freeze", 80),
            (TowerType.FLAME, "Flame", 90),
            (TowerType.TESLA, "Tesla", 120),
            (TowerType.AIR, "Air", 100),
            (TowerType.MINER, "Miner", 75),
        ]
        
        button_y = 100
        for tower_type, name, cost in tower_types:
            color = {
                TowerType.BASIC: COLORS['tower_basic'],
                TowerType.BLAST: COLORS['tower_blast'],
                TowerType.FREEZE: COLORS['tower_freeze'],
                TowerType.FLAME: COLORS['tower_flame'],
                TowerType.TESLA: COLORS['tower_tesla'],
                TowerType.AIR: COLORS['tower_air'],
                TowerType.MINER: COLORS['tower_miner'],
            }[tower_type]
            
            btn_rect = pygame.Rect(ui_panel_x + 10, button_y, 180, 40)
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=5)
            
            name_text = self.font_small.render(f"{name} ({cost})", True, 
                                              COLORS['text_primary'])
            self.screen.blit(name_text, (ui_panel_x + 20, button_y + 10))
            
            if self.selected_tower_type == tower_type:
                pygame.draw.rect(self.screen, COLORS['gold'], btn_rect, 2, border_radius=5)
            
            button_y += 50
        
        # Upgrade panel
        if self.selected_tower:
            upgrade_y = button_y + 20
            upgrade_rect = pygame.Rect(ui_panel_x + 10, upgrade_y, 180, 40)
            pygame.draw.rect(self.screen, COLORS['ui_border'], upgrade_rect, border_radius=5)
            
            upgrade_text = self.font_small.render(
                f"Upgrade Lvl {self.selected_tower.level} ({self.selected_tower.upgrade_cost}g)",
                True, COLORS['text_primary']
            )
            self.screen.blit(upgrade_text, (ui_panel_x + 20, upgrade_y + 10))
        
        # Instructions
        instr_y = self.config.screen_height - 80
        instr_text = self.font_small.render("Space: Next Wave | R: Research | Right-click: Cancel",
                                           True, COLORS['text_secondary'])
        self.screen.blit(instr_text, (20, instr_y))
    
    def draw_placement_preview(self):
        mouse_pos = pygame.mouse.get_pos()
        grid_x = mouse_pos[0] // TILE_SIZE
        grid_y = mouse_pos[1] // TILE_SIZE
        
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            color = self.get_tower_color(self.selected_tower_type)
            preview_rect = pygame.Rect(grid_x * TILE_SIZE, grid_y * TILE_SIZE,
                                      TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, color, preview_rect, 2, border_radius=5)
    
    def get_tower_color(self, tower_type: TowerType) -> Tuple[int, int, int]:
        colors = {
            TowerType.BASIC: COLORS['tower_basic'],
            TowerType.BLAST: COLORS['tower_blast'],
            TowerType.FREEZE: COLORS['tower_freeze'],
            TowerType.FLAME: COLORS['tower_flame'],
            TowerType.TESLA: COLORS['tower_tesla'],
            TowerType.AIR: COLORS['tower_air'],
            TowerType.MINER: COLORS['tower_miner'],
        }
        return colors.get(tower_type, COLORS['tower_basic'])
    
    def draw_pause_overlay(self):
        overlay = pygame.Surface((self.config.screen_width, self.config.screen_height), 
                                pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, COLORS['text_primary'])
        rect = pause_text.get_rect(center=(self.config.screen_width // 2, 
                                          self.config.screen_height // 2))
        self.screen.blit(pause_text, rect)
        
        resume_text = self.font_medium.render("Press ESC to Resume", 
                                             True, COLORS['text_secondary'])
        rect = resume_text.get_rect(center=(self.config.screen_width // 2,
                                           self.config.screen_height // 2 + 50))
        self.screen.blit(resume_text, rect)
    
    def draw_game_over(self):
        overlay = pygame.Surface((self.config.screen_width, self.config.screen_height),
                                pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font_large.render("GAME OVER", True, COLORS['red'])
        rect = game_over_text.get_rect(center=(self.config.screen_width // 2,
                                               self.config.screen_height // 2 - 50))
        self.screen.blit(game_over_text, rect)
        
        wave_text = self.font_medium.render(f"Waves Survived: {self.resource_manager.wave - 1}",
                                           True, COLORS['text_primary'])
        rect = wave_text.get_rect(center=(self.config.screen_width // 2,
                                         self.config.screen_height // 2 + 20))
        self.screen.blit(wave_text, rect)
        
        restart_text = self.font_medium.render("Press ENTER to Restart",
                                              True, COLORS['text_secondary'])
        rect = restart_text.get_rect(center=(self.config.screen_width // 2,
                                            self.config.screen_height // 2 + 70))
        self.screen.blit(restart_text, rect)
    
    def draw_research(self):
        self.screen.fill(COLORS['background'])
        
        title = self.font_large.render("RESEARCH LAB", True, COLORS['text_primary'])
        self.screen.blit(title, (self.config.screen_width // 2 - 150, 50))
        
        points_text = self.font_medium.render(
            f"Research Points: {self.research_manager.research_points}",
            True, COLORS['gold']
        )
        self.screen.blit(points_text, (self.config.screen_width // 2 - 150, 120))
        
        # Draw research nodes
        y_offset = 180
        for node_id, node in self.research_manager.nodes.items():
            color = COLORS['green'] if node.purchased else (
                COLORS['gold'] if node.unlocked else COLORS['text_secondary']
            )
            
            node_rect = pygame.Rect(100, y_offset, self.config.screen_width - 200, 60)
            pygame.draw.rect(self.screen, color, node_rect, border_radius=5, width=2)
            
            name_text = self.font_medium.render(node.name, True, COLORS['text_primary'])
            self.screen.blit(name_text, (120, y_offset + 10))
            
            desc_text = self.font_small.render(node.description, True, 
                                              COLORS['text_secondary'])
            self.screen.blit(desc_text, (120, y_offset + 35))
            
            cost_text = self.font_small.render(f"Cost: {node.cost}", True, COLORS['gold'])
            self.screen.blit(cost_text, (self.config.screen_width - 200, y_offset + 20))
            
            y_offset += 70
        
        back_text = self.font_medium.render("Press ESC to Return", 
                                           True, COLORS['text_secondary'])
        self.screen.blit(back_text, (self.config.screen_width // 2 - 100, 
                                    self.config.screen_height - 60))
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            
            if self.state == GameState.PLAYING:
                self.update(dt)
            
            self.draw()
        
        pygame.quit()
        sys.exit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
