import sys
import os
import time

import pygame
from pygame.locals import *

from engine import TextView, ViewBase, Board, Piece, Color

file = open("score.txt","r")
HIGHSCORE = file.read()
file.close()
click = False
_print_dim = False


bg_img = pygame.image.load("image/bgimg.png")
bg_img = pygame.transform.scale(bg_img,(600,600))
main_img = pygame.image.load("image/main_img.png")
main_img = pygame.transform.scale(main_img,(600,600))

start_img = pygame.image.load("image/start_menu.png")
start_img = pygame.transform.scale(start_img,(200,50))
score_img = pygame.image.load("image/score_menu.png")
score_img = pygame.transform.scale(score_img,(200,50))
exit_img = pygame.image.load("image/exit_menu.png")
exit_img = pygame.transform.scale(exit_img,(200,50))

class PygameView(ViewBase):
    """Renders a board in pygame."""

    COLOR_MAP = {
        Color.CLEAR : pygame.Color(0, 0, 0),
        Color.RED : pygame.Color(255, 0, 0),
        Color.BLUE : pygame.Color(0, 255, 0),
        Color.GREEN : pygame.Color(0, 0, 255),
        Color.YELLOW : pygame.Color(255, 255, 0),
        Color.MAGENTA : pygame.Color(255, 0, 255),
        Color.CYAN : pygame.Color(0, 255, 255),
        Color.ORANGE : pygame.Color(255, 140, 0),
        Color.GRAY : pygame.Color(189,189,189)
    }
        
    BOARD_BORDER_SIZE = 5
    SCORE_PADDING = 5
    BORDER_SIZE = 4
    BORDER_FADE = pygame.Color(0, 0, 0) # 배경 색임

    def __init__(self, surf, fonts):
        ViewBase.__init__(self)
        self.surf = surf
        self.view_width = surf.get_width()
        self.view_height = surf.get_height()
        self.box_size = 10
        self.padding = (0, 0)
        self.go_font = fonts["game_over"]
        self.sc_font = fonts["score"]
        self.go_font_color = pygame.Color(200, 0, 0)
        self.sc_font_color = pygame.Color(189,189,189)
        self.score = 0
        self.level = None

        self.end_msg = self.go_font.render("GAME OVER", True, self.go_font_color)

    # Public interface to views
    def set_size(self, cols, rows):
        ViewBase.set_size(self, cols, rows)
        self.calc_dimensions()

    def set_score(self, score):
        self.score = score

    def set_level(self, level):
        if self.level != level:
            pygame.event.post(pygame.event.Event(Tetris.LEVEL_UP, level = level))
        self.level = level

    def show(self):
        self.draw_board()
        self.show_score()

    def show_score(self):
        score_height = 0
        if self.score is not None:
            score_surf = self.sc_font.render("{:06d}".format(self.score), True, self.sc_font_color)
            self.surf.blit(score_surf, (self.BOARD_BORDER_SIZE, self.BOARD_BORDER_SIZE))
            score_height = score_surf.get_height()

        if self.level is not None:
            level_surf = self.sc_font.render("LEVEL {:02d}".format(self.level), True, self.sc_font_color)
            level_pos = (self.BOARD_BORDER_SIZE, 
                         self.BOARD_BORDER_SIZE + score_height + self.SCORE_PADDING)
            self.surf.blit(level_surf, level_pos)

    def show_game_over(self):
        r = self.end_msg.get_rect()
        self.surf.blit(self.end_msg, (300 - r.width // 2, 300 - r.height // 2))
    
    # Helper methods

    def get_score_size(self):
        (sw, sh) = self.sc_font.size("000000")
        (lw, lh) = self.sc_font.size("LEVEL 00")
        return (max(sw, lw) + self.BOARD_BORDER_SIZE, sh + lh + self.SCORE_PADDING)

    def calc_dimensions(self):
        horiz_size = (self.view_width - (self.BOARD_BORDER_SIZE * 2)) // self.width
        vert_size = (self.view_height - (self.BOARD_BORDER_SIZE * 2)) // self.height

        if vert_size > horiz_size:
            self.box_size = horiz_size
            self.padding = (self.get_score_size()[0] * 2, 
                            (self.view_height 
                                - self.BOARD_BORDER_SIZE
                                - (self.height * horiz_size)))
        else:
            self.box_size = vert_size
            left_padding = max(self.get_score_size()[0] * 2,
                               (self.view_width 
                                - self.BOARD_BORDER_SIZE 
                                - (self.width * vert_size)))
            self.padding = (left_padding, 0)

        global _print_dim
        if not _print_dim:
            print(self.width, self.height)
            print(self.view_width, self.view_height)
            print(horiz_size, vert_size)
            print(self.box_size)            
            print(self.padding)
            _print_dim = True


    def draw_board(self):
        bg_color = self.COLOR_MAP[Color.CLEAR]
        self.surf.fill(self.BORDER_FADE)
        self.surf.blit(bg_img,(0,0))

        X_START = self.BOARD_BORDER_SIZE + (self.padding[1] // 2)
        Y_START = self.BOARD_BORDER_SIZE + (self.padding[0] // 2)

        x = X_START
        y = Y_START
        board_rect = (y, x, self.width * self.box_size, self.height * self.box_size)
        pygame.draw.rect(self.surf, bg_color, board_rect)
        for col in self.rows:
            for item in col:
                self.draw_box(x, y, item)
                y += self.box_size
            x += self.box_size
            y = Y_START

    def draw_box(self, x, y, color):
        if color == Color.CLEAR:
            return

        pg_color = self.COLOR_MAP[color]
        bd_size = self.BORDER_SIZE
        bd_color = self.BORDER_FADE

        outer_rect = (y, x, self.box_size, self.box_size)
        inner_rect = (y + bd_size, x + bd_size, 
                      self.box_size - bd_size*2, self.box_size - bd_size*2)

        pygame.draw.rect(self.surf, bd_color, outer_rect)
        pygame.draw.rect(self.surf, pg_color, inner_rect)

class Tetris:
    DROP_EVENT = USEREVENT + 1
    LEVEL_UP = USEREVENT + 2

    def __init__(self, view_type):
        self.board = Board(10, 20)
        self.board.generate_piece()
        self.view_type = view_type
        self.game_over = False

        if view_type == TextView:
            def cls():
                os.system('cls')
            self.show_action = cls
            self.max_fps = 5
        else:
            self.show_action = None
            self.max_fps = 50

    def key_handler(self, key):
        if key == K_LEFT:
            self.board.move_piece(-1,0)
        elif key == K_RIGHT:
            self.board.move_piece(1, 0)
        elif key == K_UP:
            self.board.rotate_piece()
        elif key == K_DOWN:
            self.board.move_piece(0, 1)
        elif key == K_a:
            self.board.rotate_piece(clockwise=False)
        elif key == K_s:
            self.board.rotate_piece()
        elif key == K_SPACE:
            self.board.full_drop_piece()

    def init(self):
        pygame.font.init()
        pygame.mixer.init()
        pygame.display.set_caption("Tetris by LJH")
        self.surf = pygame.display.set_mode((600, 600)) # 디스플레이 크기 설정
        self.font = None

        if pygame.font.get_init():
            self.fonts = {}
            self.fonts["game_over"] = pygame.font.SysFont("freesansbold.ttf", 72)
            self.fonts["score"] = pygame.font.SysFont("freesansbold.ttf", 29)

        self.view = self.view_type(self.surf, self.fonts)

    def show_colors(self):
        self.init()

        print("Fonts:", pygame.font.get_fonts())
        n = len(Color.colors())
        self.view.set_size(n+1, 1)
        for i in range(n):
            self.view.render_tile(i + 1, 0, Color.colors()[i])
        self.view.show()

        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

    def get_level_speed(self, level):
        SPEEDS = {
            1 : 1000,
            2 : 750,
            3 : 500,
            4 : 400,
            5 : 300,
            6 : 250,
            7 : 200,
            8 : 150,
            9 : 125,
            10 : 100,
            11 : 90,
            12 : 80,
            13 : 75
        }

        if level > 13:
            return 75 - (5 * (level - 13))
        else:
            return SPEEDS[level]

    def render_frame(self):
        self.board.render(self.view)

        if self.show_action is not None:
            self.show_action()
        self.view.show()

        if self.game_over:
            self.view.show_game_over() 
        
        pygame.display.update()


    def score_board(self):
        running_board = True
        global HIGHSCORE
        self.init()
        self.clock = pygame.time.Clock()
        DISPLAYSURF = pygame.display.set_mode([600,600])
        DISPLAYSURF.fill((0,0,0))

        SCORE_font = pygame.font.Font("freesansbold.ttf", 35)
        title = SCORE_font.render("HIGH SCORE",True,(189,189,189))
        title_rect = title.get_rect()
        title_rect.center = (300,100)

        TEXT_font = pygame.font.Font("freesansbold.ttf", 35)
        text = TEXT_font.render(HIGHSCORE,True,(189,189,189))
        text_rect = text.get_rect()
        text_rect.center = (300,170)

        EXIT_font = pygame.font.Font("freesansbold.ttf", 30)
        text2 = TEXT_font.render("Press 'ESC' To Go Back",True,(255,0,0))
        text2_rect = text2.get_rect()
        text2_rect.center = (300,300)


        while running_board: #이벤트 루프
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    self.key_handler(event.key)
                    if event.key == K_ESCAPE:
                        running_board = False
            
            DISPLAYSURF.blit(main_img,(0,0))
            DISPLAYSURF.blit(title,title_rect)
            DISPLAYSURF.blit(text,text_rect)
            DISPLAYSURF.blit(text2,text2_rect)
            pygame.display.update()
            
            self.clock.tick(self.max_fps)

    def paused(self):
        running_pasued = True
        self.init()
        self.clock = pygame.time.Clock()
        PAUSED_SURFACE = pygame.display.set_mode([600,600])
        PAUSED_SURFACE.fill((0,0,0))
        TITLE_font = pygame.font.Font("freesansbold.ttf", 70)
        title = TITLE_font.render("Paused",True,(255,255,255))
        title_rect = title.get_rect()
        title_rect.center = (300,200)

        TEXT_font = pygame.font.Font("freesansbold.ttf", 40)
        text = TEXT_font.render("Press 'Q' To Continue",True,(255,0,0))
        text_rect = text.get_rect()
        text_rect.center = (300,300)

        while running_pasued: #이벤트 루프
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    self.key_handler(event.key)
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                        running_pasued = False
                    elif event.key == K_q:
                        running_pasued = False
                        self.game()

            
            PAUSED_SURFACE.blit(title,title_rect)
            PAUSED_SURFACE.blit(text,text_rect)
            pygame.display.update()
            self.clock.tick(self.max_fps)


    def game(self):
        global HIGHSCORE
        running_game = True
        self.init()
        self.clock = pygame.time.Clock()
        pygame.time.set_timer(self.DROP_EVENT, self.get_level_speed(1))
        pygame.mixer.music.load('sound/Tetris_theme.ogg')
        pygame.mixer.music.play(-1,0.0)

        while running_game: #게임 루프
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                    pygame.mixer_music.stop()

                elif event.type == KEYDOWN:
                    self.key_handler(event.key)
                    if event.key == K_ESCAPE:
                        pygame.mixer_music.stop()
                        running_game = False

                    elif event.key == K_p:
                        pygame.mixer_music.stop()
                        running_game = False
                        self.paused()
                    
                    elif event.key == K_r:
                        self.board.reset()
                        self.game_over = False
                        t = Tetris(PygameView)
                        t.main()

                elif event.type == self.DROP_EVENT:
                    self.board.drop_piece()
                elif event.type == self.LEVEL_UP:
                    pygame.time.set_timer(self.DROP_EVENT, self.get_level_speed(event.level))
                    print("new level:", event.level)

            if self.board.game_over and not self.game_over:
                self.game_over = True
                pygame.time.set_timer(self.DROP_EVENT, 0)
                pygame.mixer_music.stop()
                if self.view.score > int(HIGHSCORE):
                    score_file = open("score.txt","w+",encoding="utf8")
                    score_file.write("{:06d}".format(self.view.score))
                    HIGHSCORE = "{:06d}".format(self.view.score)
                    score_file.close()
                

                
            self.render_frame()
            self.clock.tick(self.max_fps)


    def main(self):
        global click
        self.init()
        self.clock = pygame.time.Clock()
        DISPLAYSURF = pygame.display.set_mode([600,600])
        DISPLAYSURF.fill((0,0,0))

        TITLE_font = pygame.font.Font("freesansbold.ttf", 70)
        title = TITLE_font.render("TETRIS",True,(255,255,255))
        title_rect = title.get_rect()
        title_rect.center = (300,100)
        

        while True: # 메인 메뉴 루프

            mx, my = pygame.mouse.get_pos()

            button_1 = start_img.get_rect(centerx = 300, centery= 220)
            button_2 = score_img.get_rect(centerx = 300, centery= 320)
            button_3 = exit_img.get_rect(centerx = 300, centery= 420)

            if button_1.collidepoint((mx, my)):
                if click:
                    self.game()
            if button_2.collidepoint((mx, my)):
                if click:
                    self.score_board()
            if button_3.collidepoint((mx, my)):
                if click:
                    pygame.quit()
                    sys.exit()
            
            DISPLAYSURF.blit(main_img,(0,0))
            DISPLAYSURF.blit(start_img,button_1)
            DISPLAYSURF.blit(score_img,button_2)
            DISPLAYSURF.blit(exit_img,button_3)
            
            click = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click = True
            
            DISPLAYSURF.blit(title,title_rect)

            pygame.display.update()
            self.clock.tick(10)



if __name__ == "__main__":
    t = Tetris(PygameView)
    t.main()
    #t.show_colors()