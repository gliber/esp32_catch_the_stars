from machine import Pin, PWM, Timer, I2C
import ssd1306  # Make sure to install the ssd1306 library for your OLED display
import time, math
from buzzer_music import music
from time import sleep
from font import Font
import framebuf
import random


class Button:
    NOT_PRESSED = 0
    SHORT_PRESS = 1
    LONG_PRESS = 2

    LONG_PRESS_THRESHOLD = 250  # in milliseconds

    def __init__(self, pin):
        self.button_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.last_press_time = 0
        self.last_state = False
        self.last_release_time = 0
        self.new_state = self.NOT_PRESSED
    
    def update_state(self):        
        button_state = not self.button_pin.value()
        if button_state != self.last_state:
            print(f'button {button_state}')
        self.last_state = button_state
        
        self.new_state = self.NOT_PRESSED
        
        if button_state:
            if self.last_press_time == 0:
                self.last_press_time = time.ticks_ms()
            
        else:
            if (self.last_press_time != 0):
                press_duration = time.ticks_ms() - self.last_press_time
                self.last_press_time = 0
                self.new_state = self.LONG_PRESS if press_duration > self.LONG_PRESS_THRESHOLD else self.SHORT_PRESS

    def is_pressed(self):
        return self.new_state
    
class Buzzer:
    def __init__(self, pin):
        self.buzzer_pin = PWM(Pin(pin))
        self.buzzer_pin.duty(0)
        self.mute = False
        
    def buzz(self, frequency, duration):
        if not self.mute:
            self.buzzer_pin.freq(frequency)
            self.buzzer_pin.duty(50)
            Utils.one_shot_timer(duration, self.stop)
        
    def stop(self, timer = None):
        self.buzzer_pin.duty(0)
        print("buzz stop")

    def toggle_mute(self):
        self.mute = not self.mute

class DisplayAsset:
    def __init__(self, game, x = 0, y = 0, button_handler = None):
        self.x = x
        self.y = y
        self.game = game
        self.button_handler = button_handler

    def tick(self):
        if self.button_handler is not None:
            button_state = self.game.button.is_pressed()
            if button_state != Button.NOT_PRESSED:
                self.button_handler(self, button_state)

    def draw(self):
        # Add logic for drawing the asset on the display
        pass
    
    def destroy(self):
        # Cleanup
        pass

class Ball(DisplayAsset):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.y_speed = 0  # Initial speed along the y-axis
        self.x_speed = 0
        self.energy_loss = 0.6
        self.moving = False
        self.RADIUS = 3
    
    def close_to(self, val):
        return math.fabs(val - self.RADIUS)
    
    def tick(self):
        if self.moving:
            buzz = False
            self.y = self.y + self.y_speed
            self.y_speed = (self.y_speed + self.game.GRAVITY)
       
            if self.y >= self.close_to(self.game.display.height) and math.fabs(self.x_speed) < 1 and math.fabs(self.y_speed) < 1:
                    print("stopped")
                    self.moving = False
                    self.game.ball_stopped()
                    self.y = self.close_to(self.game.display.height) - 1
                    return
          
            if self.y >= self.close_to(self.game.display.height):
                self.y = self.close_to(self.game.display.height) #- (self.y - self.game.display.height)
                # change y direction and slow down the ball
                self.y_speed = -self.y_speed * self.energy_loss
                self.x_speed = self.x_speed * self.energy_loss
                buzz = True
            #print(self.x,self.y,self.y_speed, self.x_speed)
              
            self.x = self.x + self.x_speed
            self.x_speed = self.x_speed 
            if self.x >= self.close_to(self.game.display.width):
                #self.x = self.close_to(self.game.display.width) - (self.x - self.close_to(self.game.display.width))
                self.x = self.close_to(self.game.display.width)
                # change x direction
                self.x_speed = -self.x_speed 
                buzz = True
            if self.x < self.close_to(0):
                #self.x = -self.x
                self.x = self.close_to(0)
                # change x direction
                self.x_speed = -self.x_speed 
                buzz = True
                
            if buzz:
                self.game.buzzer.buzz(2000,100)
            #print(self.x_speed, self.y_speed)
          
            
    def go(self, angle, speed):
        self.x_speed = math.cos(math.radians(angle)) * speed
        self.y_speed = math.sin(math.radians(angle)) * speed
        self.moving = True

    def draw(self):
        game.display.rect(int(self.x)-2, int(self.y)-2, 5, 5, 1)
        game.display.rect(int(self.x)-1, int(self.y)-3, 3, 7, 1)
        game.display.rect(int(self.x)-3, int(self.y)-1, 7, 3, 1)
    

class Star(DisplayAsset):
    STAR_SIZE = 3
    
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.y_speed = 0
        self.brightness = random.randint(0, self.STAR_SIZE)
        self.falling = False
    
    def tick(self):
        self.brightness = (self.brightness + 0.3) % self.STAR_SIZE
        if self.falling:
            self.y = self.y + self.y_speed
            self.y_speed = (self.y_speed + self.game.GRAVITY)
       
            if self.y >= self.game.display.height:
                    print("stopped")
                    self.falling = False
                    self.game.remove_asset(self)
            
    def fall(self):
        self.falling = True

    def draw(self):
        self.game.display.line(int(self.x - int(self.brightness)), int(self.y - int(self.brightness)),
                               int(self.x + int(self.brightness)), int(self.y + int(self.brightness)), 1)
        self.game.display.line(int(self.x + int(self.brightness)), int(self.y - int(self.brightness)),
                               int(self.x - int(self.brightness)), int(self.y + int(self.brightness)), 1)
        self.game.display.line(int(self.x - int(self.brightness)), int(self.y),
                               int(self.x + int(self.brightness)), int(self.y), 1)
        self.game.display.line(int(self.x), int(self.y - int(self.brightness)),
                               int(self.x), int(self.y + int(self.brightness)), 1)
        
class Curtain(DisplayAsset):
    def __init__(self, game):
        super().__init__(game)
        self.i = 0
    
    def tick(self):
        self.i = self.i+1
        if self.i == self.game.display.width/2:
            self.game.remove_asset(self)
            
    def draw(self):
        self.game.display.fill_rect(0, 0, int(self.game.display.width/2 - self.i), self.game.display.height, 0)
        self.game.display.fill_rect(int(self.game.display.width/2 + self.i) , 0, self.game.display.width, self.game.display.height, 0)
        
            
class Menu(DisplayAsset):
    
    FLICKER_DURATION = 500  # in milliseconds
    FLICKER_STEP_DURATION = 50  # in milliseconds
        
    def __init__(self, game, x, y, title, options):
        super().__init__(game, x, y)
        
        self.title = title
        self.options = options
        self.selected_option = 0
        self.flicker_timer = None
        self.flicker_start_time = 0
      
    def draw(self):
        y_offset = 0
        # Draw the menu title with an underline
        if self.title is not None:
            title_width = len(self.title) * Utils.CHAR_WIDTH
            self.game.display.text(self.title, self.x + 2 * Utils.CHAR_WIDTH, self.y)
            self.game.display.hline(self.x + 2 * Utils.CHAR_WIDTH, self.y + 8, title_width, 1)
            y_offset = y_offset + 4

        # Draw the menu options
        for i, (option,handler) in enumerate(self.options):
            y_offset = y_offset + 10  # Leave space after the title
            if i == self.selected_option and self.should_flicker():
                continue  # Skip drawing the selected option during flickering
            sign = "> " if i == self.selected_option else "  "
            self.game.display.text(sign + option, self.x, self.y + y_offset)

        #print("Menu is drawn on the display")

    def update_selection(self, direction):
        # Update the selected option based on the given direction (1 for down, -1 for up)
        self.selected_option = (self.selected_option + direction) % len(self.options)
        print(f'menu new selection {self.selected_option}')

    def choose_option(self):
        # Start flickering the chosen option
        self.flicker_start_time = time.ticks_ms()
        flicker_timer = Timer(1)
        flicker_timer.init(period=self.FLICKER_DURATION, mode=Timer.ONE_SHOT, callback=self.finalize_flicker)

    def should_flicker(self):
        # Check if flickering duration has elapsed
        return self.flicker_start_time >  0 and int(time.ticks_diff(time.ticks_ms(), self.flicker_start_time) / self.FLICKER_STEP_DURATION)%2

    def finalize_flicker(self, timer):
        self.flicker_start_time = 0
        (option, handler) = self.options[self.selected_option]
        if handler is not None:
            handler(self)
        

    def tick(self):
        # Handle button press to update the selected option
        button_state = self.game.button.is_pressed()
        if button_state == Button.SHORT_PRESS:
            self.update_selection(1)  # Update the selected option in the downward direction
            self.game.buzzer.buzz(2000, 100)  # Add buzzer feedback
        elif button_state == Button.LONG_PRESS:
            self.choose_option()  # Choose the selected option and start flickering
            self.game.buzzer.buzz(1000, 200)  # Add buzzer feedback

class FadingText(DisplayAsset):
    FADE_COUNT = 15
    
    def __init__(self, game, x, y, text):
        super().__init__(game, x, y)
        self.text = text
        self.x = self.x - int(Utils.text_width(text)/2)
        if self.x + Utils.text_width(text) > self.game.display.width:
            self.x = self.game.display.width - Utils.text_width(text)
        self.y = self.y - 8
        if (self.y < 0):
            self.y = self.FADE_COUNT
        self.count = 0
    
    def draw(self):
        self.game.display.text(self.text, self.x, self.y, 1)
        self.y = self.y - 1
        self.count = self.count + 1
        if self.count == self.FADE_COUNT:
            self.destroy()
        
    def destroy(self):
        #super.destroy(self)
        self.game.remove_asset(self)

class Bar(DisplayAsset):
    def __init__(self, game, x, y, max_value=7, value = 0):
        super().__init__(game,x, y)
        self.max_value = max_value  # Total number of fill iterations
        self.WIDTH = 20
        self.HEIGHT = 5
        self.value = 1  # Current iteration count
        self.timer = Timer(2)  # Create a new timer
        self.timer.init(period=400, mode=Timer.PERIODIC, callback=self.update_fill)  # Set timer callback

    def draw(self):
        # Draw the rectangle with the current fill level
        self.game.display.rect(self.x, self.y, self.WIDTH+2 , self.HEIGHT , 1)
        self.game.display.fill_rect(self.x+1, self.y, int(self.WIDTH*self.value /self.max_value), self.HEIGHT , 1)

    def update_fill(self, timer):
        # Update the fill level
        self.value = (self.value+1)% (self.max_value+1)
    
    def destroy(self):
        self.timer.deinit()
     
class SlidingText(DisplayAsset):
    def __init__(self, game, y, text, speed, size=1, from_right=False, button_handler = None):
        super().__init__(game, 0, y, button_handler)
        self.text = text
        self.speed = speed
        self.from_right = from_right
        self.size = size
        self.font = Font(game.display)
        self.x = self.calculate_starting_position()

    def calculate_text_width(self):
        # Calculate the width of the text based on the number of characters and font size
        return len(self.text) * 8#(self.size-8)/2+8  

    def calculate_starting_position(self):
        # Calculate the starting position based on the direction
        if self.from_right:
            return self.game.display.width
        else:
            return -self.calculate_text_width()

    def draw(self):
        # Draw the text at the current position with the specified size
        #print(self.size)
        self.font.text(self.text, int(self.x), self.y, self.size)

    def tick(self):
        super().tick()
        # Update the position of the text
        if self.from_right:
            if self.x > (self.game.display.width - self.calculate_text_width()) / 2:
                self.x -= self.speed            
        else:
            if self.x < (self.game.display.width - self.calculate_text_width()) / 2:
                self.x += self.speed

class Utils():
    
    CHAR_WIDTH = 8
    
    def dist(x1,y1,x2,y2):
        return math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2))
    
    def text_width(text, size = 8):
        # Calculate the width of the text based on the number of characters and font size
        return len(text) * size  

    def assets_distance(asset1, asset2):
        return math.sqrt((asset1.x-asset2.x)*(asset1.x-asset2.x)+(asset1.y-asset2.y)*(asset1.y-asset2.y))
    
    def one_shot_timer(duration, callback):
        print("start timer")
        timer = Timer(3)
        timer.init(period=duration, mode=Timer.ONE_SHOT, callback=callback)
        
    def load_pbm(file):
        with open(file, 'rb') as f:
            f.readline() # Magic number
            dim = f.readline().decode("utf-8").split() # Dimensions
            width = int(dim[0])
            height= int(dim[1])
            data = bytearray(f.read())
            print(f'loaded file {file}. width {width}, height {height}')
        return (data, width, height)
    
    def load_animation(file, num_of_sprites, flip):
        frames = []
        (all_frames, width, height) = Utils.load_pbm(file)

        frame_width = int(width / num_of_sprites)
        for i in range(num_of_sprites):
            frame_data = bytearray()
                
            for y in range(height):
                row_start = (i * frame_width) + (y * width)
                row_end = row_start + frame_width
                row_start = int(row_start /8)
                row_end = int(row_end / 8)
                current_data = all_frames[row_start:row_end]
                frame_data.extend(current_data)
            framebuffer = framebuf.FrameBuffer(frame_data, frame_width, height, framebuf.MONO_HLSB)
            frames.append(framebuffer)
        return (frames, frame_width, height)


class Score(DisplayAsset):
    def __init__(self, game):
        super().__init__(game, 5, 5)
        self.value = 0
    
    def add(self, add_score):
        self.value = self.value + add_score

    def draw(self):
        self.game.display.text(str(self.value), self.x, self.y)

class Bitmap(DisplayAsset):
    def __init__(self, game, x, y, file, button_handler = None):
        super().__init__(game, x, y, button_handler)
        (data, self.width, self.height) = Utils.load_pbm(file)
        self.frame = framebuf.FrameBuffer(data, self.width, self.height, framebuf.MONO_HLSB)
    
    def draw(self):
        self.game.display.blit(self.frame,self.x,self.y,0)

class Animation(DisplayAsset):
    def __init__(self, game, x, y, file, num_of_sprites, flip = False, animation_speed = 3):
        super().__init__(game, x, y)
        (self.frames, self.width, self.height) = Utils.load_animation(file, num_of_sprites, flip)
        self.current_frame = 0
        self.animation_speed = animation_speed
        
    def tick(self):
        self.current_frame = self.current_frame + 1 / self.animation_speed
        
    def draw(self):
        frame_id = int(self.current_frame) % len(self.frames)
        self.game.display.blit(self.frames[frame_id],int(self.x),int(self.y),0)

class SlidingAnimation(Animation):
    def __init__(self, game, y, file, num_of_sprites, x_change, flip = False, animation_speed = 3, callback = None):
        super().__init__(game, 0, y, file, num_of_sprites, flip, animation_speed)
        self.x_change = x_change
        if (x_change < 0):
            self.x = self.game.display.width
        else:
            self.x = -self.width
        self.callback = callback
        print(f'animal {self} x = {self.x}, change = {self.x_change}')
    
    def tick(self):
        super().tick()
        self.x += self.x_change / self.animation_speed
        if (self.x_change > 0 and self.x >= self.game.display.width) or (self.x_change < 0 and self.x < -self.width):
            print(f'animal done')
            if self.callback is not None:
                self.callback(self)
            self.game.remove_asset(self)
                
    def draw(self):
        super().draw()
            
class Cue(DisplayAsset):
    MIN_ANGLE = -10
    MAX_ANGLE = -80
    ANGLE_STEP = 10
    INITIAL_ANGLE = -40
    
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.angle = -40        
        self.MIN_GAP = 5
        self.MAX_GAP = 15
        self.gap_step = 1
        self.gap = self.MAX_GAP
        self.cue_size = 20
        self.angle_step = self.ANGLE_STEP
        
    def tick(self):
        if self.gap == self.MAX_GAP or self.gap == self.MIN_GAP:
            self.gap_step = -self.gap_step
        self.gap = self.gap + self.gap_step
        button_state = self.game.button.is_pressed()
        if button_state == Button.SHORT_PRESS:
            self.angle = self.angle + self.angle_step 
            if self.angle == self.MIN_ANGLE or self.angle == self.MAX_ANGLE:
                self.angle_step  = -self.angle_step 
            print(f"angle {self.angle}")
        elif button_state == Button.LONG_PRESS:
            print("shoot")
            self.game.shoot(self.angle)
                
    def draw(self):
    
        def angle_point(x, y, angle, radius):
            x1 = int(x - math.cos(math.radians(angle)) * radius)
            y1 = int(y - math.sin(math.radians(angle)) * radius)
            return (x1, y1)
        
        # draw cue
        for i in range(-1,2): # 3 pixels wide
            for j in range(-1,2):
                (x1, y1) = angle_point(self.x + i, self.y + j, self.angle, self.gap)
                (x2, y2) = angle_point(self.x + i, self.y + j, self.angle, self.cue_size + self.gap)
                self.game.display.line(x1, y1, x2, y2, 1)
        
        # draw dots for the ball direction    
        for i in range(1,20,4):
            (x1, y1) = angle_point(self.x, self.y, self.angle + 180, i)
            self.game.display.pixel(x1, y1, 1)
        
            
class Border(DisplayAsset):
    def __init__(self, game):
        super().__init__(game)

    def draw(self):
        # Draw a rectangle around the screen border
        width, height = self.game.display.width, self.game.display.height
        #self.game.display.rect(0, 0, width, height, 1)
        self.game.display.hline(0, height - 1, width, 1)
        self.game.display.vline(0, 0, height, 1)
        self.game.display.vline(width - 1, 0, height, 1)
        
class Game:
    GRAVITY = 0.2
    
    def __init__(self, oled_display, button_pin, buzzer_pin):
        self.display = oled_display
        self.button = Button(button_pin)
        self.buzzer = Buzzer(buzzer_pin)
        self.assets = []
        
    def add_asset(self, asset):
        self.assets.append(asset)

    def remove_asset(self, asset):
        if asset is not None and asset in self.assets:
            self.assets.remove(asset)
    
    def clear_assets(self):
        self.assets = []
        
    def tick(self):
        for asset in self.assets:
            asset.tick()  # Update each asset's state

    def draw(self):
        # Clear the display before rendering
        self.display.fill(0)
        
        # Draw each asset
        for asset in self.assets:
            asset.draw()

        # Refresh the display
        self.display.show()

class CatchTheStarsGame(Game):
    
    NUM_STARS = 5
    NUM_BALLS = 7
    SOUND_END_GAME = '0 B4 2 0;3 B4 1 0;5 B4 1 0;7 B4 2 0;10 D#4 2 0;13 C#4 2 0;16 B4 2 0;19 E4 2 0'
    
    SOUND_STAR_CAUGHT = '0 E5 1 0;2 G5 1 0;4 C6 2 0'
    #MUSIC = '10 B5 1 0;12 E6 2 0'
    
    #MUSIC = '10 E7 2 0;10 G7 2 0;10 C7 2 0;13 E7 2 0;13 G7 2 0;13 C7 2 0'
    
    #MUSIC = '10 C7 2 0;13 C7 4 0'
    #MUSIC = '0 D4 8 0;0 D5 8 0;0 G4 8 0;8 C5 2 0;10 B4 2 0;12 G4 2 0;14 F4 1 0;15 G4 17 0;16 D4 8 0;24 C4 8 0'
    
    MUSIC = '0 E3 1 0;2 E4 1 0;4 E3 1 0;6 E4 1 0;8 E3 1 0;10 E4 1 0;12 E3 1 0;14 E4 1 0;16 A3 1 0;18 A4 1 0;20 A3 1 0;22 A4 1 0;24 A3 1 0;26 A4 1 0;28 A3 1 0;30 A4 1 0;32 G#3 1 0;34 G#4 1 0;36 G#3 1 0;38 G#4 1 0;40 E3 1 0;42 E4 1 0;44 E3 1 0;46 E4 1 0;48 A3 1 0;50 A4 1 0;52 A3 1 0;54 A4 1 0;56 A3 1 0;58 B3 1 0;60 C4 1 0;62 D4 1 0;64 D3 1 0;66 D4 1 0;68 D3 1 0;70 D4 1 0;72 D3 1 0;74 D4 1 0;76 D3 1 0;78 D4 1 0;80 C3 1 0;82 C4 1 0;84 C3 1 0;86 C4 1 0;88 C3 1 0;90 C4 1 0;92 C3 1 0;94 C4 1 0;96 G2 1 0;98 G3 1 0;100 G2 1 0;102 G3 1 0;104 E3 1 0;106 E4 1 0;108 E3 1 0;110 E4 1 0;114 A4 1 0;112 A3 1 0;116 A3 1 0;118 A4 1 0;120 A3 1 0;122 A4 1 0;124 A3 1 0;0 E6 1 1;4 B5 1 1;6 C6 1 1;8 D6 1 1;10 E6 1 1;11 D6 1 1;12 C6 1 1;14 B5 1 1;0 E5 1 6;4 B4 1 6;6 C5 1 6;8 D5 1 6;10 E5 1 6;11 D5 1 6;12 C5 1 6;14 B4 1 6;16 A5 1 1;20 A5 1 1;22 C6 1 1;24 E6 1 1;28 D6 1 1;30 C6 1 1;32 B5 1 1;36 B5 1 1;36 B5 1 1;37 B5 1 1;38 C6 1 1;40 D6 1 1;44 E6 1 1;48 C6 1 1;52 A5 1 1;56 A5 1 1;20 A4 1 6;16 A4 1 6;22 C5 1 6;24 E5 1 6;28 D5 1 6;30 C5 1 6;32 B4 1 6;36 B4 1 6;37 B4 1 6;38 C5 1 6;40 D5 1 6;44 E5 1 6;48 C5 1 6;52 A4 1 6;56 A4 1 6;64 D5 1 6;64 D6 1 1;68 D6 1 1;70 F6 1 1;72 A6 1 1;76 G6 1 1;78 F6 1 1;80 E6 1 1;84 E6 1 1;86 C6 1 1;88 E6 1 1;92 D6 1 1;94 C6 1 1;96 B5 1 1;100 B5 1 1;101 B5 1 1;102 C6 1 1;104 D6 1 1;108 E6 1 1;112 C6 1 1;116 A5 1 1;120 A5 1 1;72 A5 1 6;80 E5 1 6;68 D5 1 7;70 F5 1 7;76 G5 1 7;84 E5 1 7;78 F5 1 7;86 C5 1 7;88 E5 1 6;96 B4 1 6;104 D5 1 6;112 C5 1 6;120 A4 1 6;92 D5 1 7;94 C5 1 7;100 B4 1 7;101 B4 1 7;102 C5 1 7;108 E5 1 7;116 A4 1 7'
    SPLASH = "splash3-mono.pbm"
       
    def __init__(self, oled_display, button_pin, buzzer_pin):
        super().__init__(oled_display, button_pin, buzzer_pin)
         # Add any additional initialization code here
        #self.initialize_assets()        
        self.stars = []
        self.animal = None
        self.music_mute = False
        
        self.high_score = 0
        #self.music = None 
        self.music = music(self.MUSIC, pins=[Pin(23)], tempo=2)
       
    def play(self):
    # Main game loop
        print("play")
        self.show_splash()
        while True:
            game.tick()  # Update game state    
            game.draw()  # Render the game on the OLED display
            
    def add_animal(self):
        ANIMALS = [{"file": 'bird.pbm', "num_frames" : 8, "y" : -10, "speed" : -5},
                   {"file": 'cat.pbm', "num_frames" : 6, "y" : 16, "speed" : 5},
                   {"file": 'bird3.pbm', "num_frames" : 6, "y" : -10, "speed" : 5},
                   {"file": 'dog2.pbm', "num_frames" : 6, "y" : 16, "speed" : 5}]
        
        animal = random.randint(0, len(ANIMALS)-1)
        print(f'new animal {animal}')
        self.animal = SlidingAnimation(self,
                                       ANIMALS[animal]["y"],
                                       ANIMALS[animal]["file"],
                                       ANIMALS[animal]["num_frames"],
                                       ANIMALS[animal]["speed"])
        self.add_asset(self.animal)
    
    def show_splash(self, caller = None, button_pressed = None):
        print("show splash")
        self.clear_assets()
        self.add_asset(Bitmap(self,0,0,self.SPLASH, button_handler = self.main_menu))
        self.add_asset(Curtain(self))
        
    def main_menu(self, splash_caller, button_pressed = None):
        print("show menu")
        self.clear_assets()
        menu_options = [("Start Game", self.show_instructions1),
                        ("Options", self.options_menu)]
        self.add_asset(Menu(self, 10, 13, "Hi there!", menu_options))
        self.add_asset(Star(self, 10,10))
        self.add_asset(Star(self, 110,5))
        self.add_asset(Star(self, 80,60))
        self.add_asset(Star(self, 15,55))
        
    def options_menu(self, main_menu_caller):
        print("show options menu")
        self.remove_asset(main_menu_caller)
        menu_options = [("Music On/Off", self.toggle_music),
                        ("Sound On/Off", self.toggle_sound),
                        ("Back", self.main_menu)]
        self.add_asset(Menu(self, 10, 10, "Options", menu_options))
        
    def toggle_sound(self, menu):
        print('sound on/off')
        self.buzzer.toggle_mute()

    def toggle_music(self, menu):
        self.music_mute = not self.music_mute
        print(f'music mute: {self.music_mute}')
        if self.music_mute:
            self.music = None
            #music('', looping = False)
            self.buzzer.stop()
        else:
            self.music = music(self.MUSIC, pins=[Pin(23)])
        
            
    def show_instructions1(self, caller = None):
        self.clear_assets()
        self.add_asset(SlidingText(self, 10, "Catch all stars", 8, button_handler = self.show_instructions2))  # Add the SlidingText asset
        self.add_asset(SlidingText(self, 30, "With 7 balls!", 8))  # Add the SlidingText asset
    
    def show_instructions2(self,  caller = None, button_pressed = None):
        self.clear_assets()
        self.add_asset(SlidingText(self, 8, "Use the button:", 8, from_right = True, button_handler = self.show_high_score))  # Add the SlidingText asset        
        self.add_asset(SlidingText(self, 24, "Short to aim", 8, from_right = True))  # Add the SlidingText asset
        self.add_asset(SlidingText(self, 40, "Long to shoot", 8, from_right = True))  # Add the SlidingText asset
    
    def show_high_score(self,  caller = None, button_pressed = None):
        self.clear_assets()
        self.add_asset(SlidingText(self, 10, "Ready?", 8, button_handler = self.start_game))  # Add the SlidingText asset        
        self.add_asset(SlidingText(self, 30, f"High score is {self.high_score}", 8))  # Add the SlidingText asset
        
    def start_game(self,  caller = None, button_pressed = None):
        #self.remove_asset(menu)
        self.clear_assets()
        #self.init_assets()
        self.score = Score(self)
        self.add_asset(self.score)
        
        self.balls = []
        
        self.start_level()
        
    def start_level(self,  caller = None, button_pressed = None):
        print("start level")
        # remove animal from screen if exists
        self.remove_asset(self.animal)
        self.animal = None
        
        if caller is not None:
            self.remove_asset(caller)
        
        self.add_asset(Border(self))
        
        self.stars = []
        while len(self.stars) < self.NUM_STARS:
            star = Star(self, random.randint(35,self.display.width-5), random.randint(10,self.display.height-20))
            # check that this new star isn't too close to the other stars
            collision = False
            for other_star in self.stars:
                if Utils.assets_distance(star, other_star) < 7:
                    collision = True
                    print("collision")
            if not collision:
                self.stars.append(star)
                self.add_asset(star)
        
        self.new_ball()
        
    def new_ball(self):        
        self.ball = Ball(self, 20, 40)
        self.add_asset(self.ball)
        self.balls.append(self.ball)
        print(f'num balls {len(self.balls)}')
        
        self.cue = Cue(self, 20, 40)
        self.add_asset(self.cue)

        self.speed_bar = Bar(self,3,20)
        self.add_asset(self.speed_bar)
        
        self.stars_caught_with_current_ball = 0
        
        #print(f"ball {self.ball}")
     
    def tick(self):
        # general game tick
        super().tick()
        self.check_collisions()
        self.button.update_state()
        if self.music is not None:
            self.music.tick()
        
    def check_collisions(self):
        for star in self.stars:
            #print(f'dist {star}:{self.ball} - {Utils.assets_distance(star, self.ball)}')
            if Utils.assets_distance(star, self.ball) <= self.ball.RADIUS*2:                
                self.stars_caught_with_current_ball = self.stars_caught_with_current_ball + 1
                add_score = self.stars_caught_with_current_ball
                self.add_asset(FadingText(self,star.x,star.y, f"+{add_score}"))
                self.score.add(add_score)
                star.fall()
                self.stars.remove(star)
                #self.buzzer.buzz(4000,100)
                if self.music_mute:
                    self.music = music(self.SOUND_STAR_CAUGHT, pins=[Pin(23)], tempo=1, looping = False)
                
    def shoot(self, angle):
        self.remove_asset(self.cue)
        self.ball.go(angle, self.speed_bar.value)
        self.remove_asset(self.speed_bar)

    def ball_stopped(self):
        print(f'stars left {len(self.stars)}')
        if len(self.balls) == self.NUM_BALLS:
            self.end_game()
        elif len(self.stars) == 0:
            self.level_completed()
        else:
            self.new_ball()
        
    def level_completed(self):
        self.add_asset(SlidingText(self, 23, "More stars!", 8,button_handler = self.start_level))  # Add the SlidingText asset
        self.add_animal()
        if self.music_mute:
            self.music = music(self.SOUND_END_GAME, pins=[Pin(23)], tempo=2, looping = False)
                
    def end_game(self):
        self.remove_asset(self.score)
        for star in self.stars:
            self.remove_asset(star)
        if (self.score.value > self.high_score):            
            self.add_asset(SlidingText(self, 10, "New high score!", 4))  # Add the SlidingText asset
            self.high_score = self.score.value
        else:
            self.add_asset(SlidingText(self, 10, "Game over", 4))  # Add the SlidingText asset
        self.add_asset(SlidingText(self, 30, f"Your score: {self.score.value}", 4, from_right = True, button_handler = self.show_splash))  # Add the SlidingText asset
        if self.music_mute:
            self.music = music(self.SOUND_END_GAME, pins=[Pin(23)], tempo=2, looping = False)


if __name__ == "__main__":
    # Initialize I2C for OLED display
    i2c = I2C(-1, scl=Pin(22), sda=Pin(21))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)

    game = CatchTheStarsGame(oled, 4, 23)
    game.play()
