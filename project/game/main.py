import os
import pygame

# инициализация окна pygame
pygame.init()
pygame.display.set_caption('SUPER MEGA ULTRA ALPHA PLATFORMER')
size = width, height = 800, 600
screen = pygame.display.set_mode(size)

# константы
cellSize = 35 

JUMP_POWER = 6.5
ACC_G = 0.3
MOVE_SPEED = 2.1

LVLS_COUNT = 3

spriteSpeed = 9

all_sprites = pygame.sprite.Group()
time = 0

# звуки и музыка
pygame.mixer.music.load('music/soundtrack.mp3')
pygame.mixer.music.set_volume(0.15)
pygame.mixer.music.play()

soundCollect = pygame.mixer.Sound("music/sound_collect.mp3")
soundDeath = pygame.mixer.Sound("music/sound_death.mp3")
soundWin = pygame.mixer.Sound("music/sound_win.mp3")

# флаги для клавишь
keys = {
	"up": False,
	"down": False,
	"left": False,
	"right": False,
}

# функция для рисования текста средствами pygame
def drawText(txt, x, y, color, fontSize = 50, center = True):
	font = pygame.font.Font(None, fontSize)
	text = font.render(txt, True, color)
	
	text_x = x
	text_y = y
	if center:
		text_x -= text.get_width() // 2
		text_y -= text.get_height() // 2
	
	screen.blit(text, (text_x, text_y))

# загрузить изображение
def load_image(name, colorkey=None):
	fullname = os.path.join('imgs', name)
	try:
		image = pygame.image.load(fullname)
	except pygame.error as message:
		print('Cannot load image:', name)
		raise SystemExit(message)
	if colorkey == -1:
		colorkey = image.get_at((0, 0))
		image.set_colorkey(colorkey)
	elif colorkey != None:
		colorkey = image.get_at(colorkey)
		image.set_colorkey(colorkey)
	image = image.convert_alpha()
	return image

# текстуры тайлов
tiles_imgs = {
	".": [load_image("empty.png")],
	"e": [
		load_image("finish1.png", colorkey=(8, 34)),
		load_image("finish2.png", colorkey=(8, 34)),
		load_image("finish3.png", colorkey=(8, 34)),
	],
	"x": [load_image("wall.png")],
	"c": [
		load_image("coin1.png", colorkey=-1),
		load_image("coin2.png", colorkey=-1),
		load_image("coin3.png", colorkey=-1),
		load_image("coin2.png", colorkey=-1),
	],
	"s": [load_image("spikes.png", colorkey=-1)],
	"b": [load_image("spikes_blood.png", colorkey=-1)],
	"o": [load_image("opacity.png", colorkey=-1)],
}

# загрузить данные уровня
# формат:
# . - пустое пространство
# x - стена
# e - выход
# p - начальная позиция игрока
# c - монета
# s - шипы

def loadLevel (name):
	file = open(os.path.join("lvlData", name), "r")
	lvlData = [i.strip() for i in file]
	max_width = max(map(len, lvlData))
	return list(map(lambda x: x.ljust(max_width, '.'), lvlData))

# тайл
class Tile(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		super().__init__()
		self.imgs = tiles_imgs[img]
		self.img = 0

		self.image = self.imgs[self.img]
		self.mask = pygame.mask.from_surface(self.image)

		self.rect = self.image.get_rect()

		offsetX = (cellSize - self.rect.width) / 2
		offsetY = (cellSize - self.rect.height) / 2

		self.rect.x = x * cellSize + offsetX
		self.rect.y = y * cellSize + offsetY

		self.collected = False

	# восстановить собранную монету (только для монет)
	def aliveCoin(self):
		super().__init__()
		self.imgs = tiles_imgs["c"]
		self.img = 0

		self.image = self.imgs[self.img]
		self.mask = pygame.mask.from_surface(self.image)
		self.collected = False

	# заменить текстуру шипа (только для шипов)
	def blood(self):
		self.imgs = tiles_imgs["b"]
		self.image = self.imgs[self.img]
		self.mask = pygame.mask.from_surface(self.image)

	# собрать монету (только для монет)
	def collect(self):
		self.imgs = tiles_imgs["o"]
		self.image = self.imgs[0]
		self.collected = True

	# обновить кадр анимации спрайта
	def update(self):
		if time % spriteSpeed == 0:
			self.img = (self.img + 1) % len(self.imgs)
			self.image = self.imgs[self.img]

		self.mask = pygame.mask.from_surface(self.image)

# уровень
class Level:
	def __init__(self, lvlData):
		self.lvlData = lvlData

	# загрузить уровень из данных уровня
	def load(self):
		lvlData = self.lvlData

		self.width = len(lvlData[0])
		self.height = len(lvlData)

		self.walls = []
		self.coins = []
		self.spikes = []
		self.exit = None

		self.sprites = pygame.sprite.Group()

		playerCoords = [0, 0]

		for y in range(self.height):
			for x in range(self.width):
				sgn = lvlData[y][x]
				if sgn == "c" or sgn == "p" or sgn == "e" or sgn == "s":
					self.sprites.add(Tile(".", x, y))

				if sgn == "p":
					playerCoords = [x, y]
					continue

				tile = Tile(sgn, x, y)
				self.sprites.add(tile)
				
				if sgn == "c":
					self.coins.append(tile)

				if sgn == "x":
					self.walls.append(tile)

				if sgn == "s":
					self.spikes.append(tile)

				if sgn == "e":
					self.exit = tile

		return playerCoords

	# нарисовать уровень
	def draw(self, camera):
		for i in self.sprites:
			i.update()
			screen.blit(i.image, camera.apply(i))

# игрок
class Player(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.width = 18
		self.height = 32

		self.sprites = {
			"stand": load_image("player_stand.png", colorkey=-1),
			"walk": [load_image("player_walk_1.png", colorkey=-1), load_image("player_walk_2.png", colorkey=-1)],
		}

		self.image = self.sprites["stand"]
		self.imageNum = 0
		self.mask = pygame.mask.from_surface(self.image)

		self.rect = self.image.get_rect()
		self.rect.x = 0
		self.rect.y = 0

		self.dir = "right"

		self.velx = 0
		self.vely = 0

		self.onGround = False

		all_sprites.add(self)

		self.score = 0

	# обновить спрайт в зависимости от состояния
	def updateImage(self):
		if time % spriteSpeed == 0:
			self.imageNum = (self.imageNum + 1) % len(self.sprites["walk"])

		if self.velx == 0:
			self.image = self.sprites["stand"]
		else:
			self.image = self.sprites["walk"][self.imageNum]

		if self.dir == "left":
			self.image = pygame.transform.flip(self.image, True, False)

		self.mask = pygame.mask.from_surface(self.image)

	# переместить в указанную позицию
	def setCoords(self, x, y):
		self.rect.x = (cellSize - self.width) / 2 + x * cellSize
		self.rect.y = (cellSize - self.height) + y * cellSize
		self.vely = self.velx = 0

	def getCollideRect(self, rects):
		for i in rects:
			if pygame.sprite.collide_rect(self, i):
				return i.rect

		return False

	# обработка столкновений со стенами
	def collisionX(self, rects):
		rect = self.getCollideRect(rects)

		if not rect:
			return 

		if self.velx > 0:                      
			self.rect.right = rect.left 

		if self.velx < 0:                      
			self.rect.left = rect.right

	def collisionY(self, rects):
		rect = self.getCollideRect(rects)

		if not rect:
			return 

		if self.vely > 0:                      
			self.rect.bottom = rect.top 
			self.onGround = True          
			self.vely = 0                 

		if self.vely < 0:                      
			self.rect.top = rect.bottom 
			self.vely = 0

	# обработка столкновений с другими объектами
	def collideCoins(self, coins):
		collect = False
		for i in coins:
			if pygame.sprite.collide_mask(self, i) and not i.collected:
				i.collect()
				self.score += 10
				collect = True

		if collect:
			soundCollect.play()

	def collideExit(self, exit):
		return pygame.sprite.collide_mask(self, exit)

	def collideSpikes(self, spikes):
		for i in spikes:
			if pygame.sprite.collide_mask(self, i):
				i.blood()
				return True

		return False

	# переместить игрока
	def move(self, walls, coins, spikes, exit):
		if self.onGround and keys["up"]:
			self.vely = -JUMP_POWER
		elif not self.onGround:
			self.vely += ACC_G
		else:
			self.vely = 0

		if keys["left"]:
			self.velx = -MOVE_SPEED
			self.dir = "left"
		elif keys["right"]:
			self.velx = MOVE_SPEED
			self.dir = "right"
		else:
			self.velx = 0

		self.updateImage()

		self.onGround = False

		self.rect.x += self.velx
		self.collisionX(walls)
		self.rect.y += self.vely
		self.collisionY(walls)

		self.collideCoins(coins)

		death = self.collideSpikes(spikes)
		win = self.collideExit(exit)

		if death:
			return "fail"

		if win:
			return "win"

# камера
class Camera:
	def __init__(self, width, height):
		self.x = 0
		self.y = 0
		self.offsetX = width / 2
		self.offsetY = height / 2

	def setCoords(self, x, y):
		self.x = x
		self.y = y

	def apply(self, target):
		return target.rect.move(-self.x + self.offsetX, -self.y + self.offsetY)

class Game:
	def __init__(self):
		self.player = Player()
		self.camera = Camera(width, height)
		self.status = "intro"
		self.score = 0

		with open("gameData/data.txt", "r") as file:
			data = file.read()
			self.highScore = int(data) if data != "" else 0

		self.currentLvl = -1

		self.lvls = self.loadLevels(LVLS_COUNT)

	# загрузка уровней
	def loadLevels(self, lvlsCount):
		res = []
		for i in range(lvlsCount):
			res.append(Level(loadLevel("level" + str(i) + ".txt")))

		return res

	# загрущить следующий уровень
	def nextLevel(self):
		if self.currentLvl >= LVLS_COUNT:
			return

		self.player.score = 0
		self.currentLvl += 1
		self.playerCoords = self.lvls[self.currentLvl].load()
		self.player.setCoords(self.playerCoords[0], self.playerCoords[1])

	# перезапустить уровень
	def restartLevel(self):
		self.player.score = 0
		for i in self.lvls[self.currentLvl].coins:
			i.aliveCoin()

		self.player.setCoords(self.playerCoords[0], self.playerCoords[1])

	def drawIntroScreen(self):
		screen.fill((0, 0, 0))
		drawText("SUPER MEGA ULTRA ALPHA PLATFORMER", width // 2, height // 2 - 50, (255, 255, 200))
		drawText("by Smoking Elk", width // 2, height // 2 + 50, (255, 255, 200), 30)

	def drawWinScreen(self):
		screen.fill((0, 0, 0))
		drawText("YOU WIN", width // 2, height // 2 - 50, (255, 255, 200))
		drawText("your score: " + str(self.score), width // 2, height // 2 + 50, (255, 255, 200), 30)
		drawText("high score: " + str(self.highScore), width // 2, height // 2 + 80, (255, 255, 200), 30)

	def gameOverScreen(self):
		screen.fill((0, 0, 0))
		drawText("GAME OVER", width // 2, height // 2, (255, 255, 200))

	def drawCompleteScreen(self):
		screen.fill((0, 0, 0))
		drawText("LEVEL " + str(self.currentLvl + 1) + " COMPLETE", width // 2, height // 2, (255, 255, 200))

	def drawScore(self):
		drawText("Score: " + str(self.player.score), 10, 10, (255, 255, 200), fontSize=25, center=False)

	# главный игровой цикл
	def updateGameplay(self):
		lvl = self.lvls[self.currentLvl]

		response = self.player.move(lvl.walls, lvl.coins, lvl.spikes, lvl.exit)
		if response == "win":
			self.score += self.player.score
			self.status = "complete"
			pygame.mixer.music.pause()
			soundWin.play()
		elif response == "fail":
			self.status = "gameOver"
			pygame.mixer.music.pause()
			soundDeath.play()
			return

		self.camera.setCoords(self.player.rect.x, self.player.rect.y)
		lvl.draw(self.camera)

		for i in all_sprites:
			screen.blit(i.image, self.camera.apply(i))

		self.drawScore()

	# при клике мышью
	def onclick(self):

		if self.status == "gameOver":
			self.status = "game"
			pygame.mixer.music.play()
			self.restartLevel()
			return

		if self.status == "win":
			self.currentLvl = -1
			self.status = "intro"
			self.score = 0
			return

		if self.status == "complete":
			pygame.mixer.music.play()

		if self.status == "complete" and self.currentLvl == LVLS_COUNT - 1:
			self.status = "win"
			self.highScore = max(self.highScore, self.score)

			with open("gameData/data.txt", "w") as file:
				file.write(str(self.highScore))

			return

		if self.status == "game":
			return

		if self.status == "intro" or self.status == "complete":
			self.nextLevel()
			self.status = "game"
			return

	# показать нужную сцену в зависимости от состояния игры
	def update(self):
		if self.status == "intro":
			self.drawIntroScreen()
			return

		if self.status == "game":
			self.updateGameplay()
			return

		if self.status == "complete":
			self.drawCompleteScreen()
			return

		if self.status == "win":
			self.drawWinScreen()
			return

		if self.status == "gameOver":
			self.gameOverScreen()
			return

game = Game()

clock = pygame.time.Clock()
frameRate = 60
running = True

# игровой цикл
while running:
	time += 1
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

		if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
			keys["left"] = True
		if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
			keys["right"] = True

		if event.type == pygame.KEYUP and event.key == pygame.K_d:
			keys["right"] = False
		if event.type == pygame.KEYUP and event.key == pygame.K_a:
			keys["left"] = False

		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			keys["up"] = True

		if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
			keys["up"] = False

		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			running = False

		if event.type == pygame.MOUSEBUTTONUP:
			game.onclick()
		
	screen.fill((0, 0, 0))

	game.update()

	pygame.display.flip()
	clock.tick(frameRate)

# выход из приложения
pygame.quit()