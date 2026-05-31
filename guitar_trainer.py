import pygame
import sys
import sounddevice as sd
import numpy as np
import random
import json
import os
from datetime import datetime

# Notes
guitar_strings = {
    "E2": 82.41, "A2": 110.00, "D3": 146.83, 
    "G3": 196.00, "B3": 246.94, "E4": 329.63
}

master_notes = [
    ("E2", 82.41), ("F2", 87.31), ("F#2", 92.50), ("G2", 98.00), 
    ("G#2", 103.83), ("A2", 110.00), ("A#2", 116.54), ("B2", 123.47), 
    ("C3", 130.81), ("C#3", 138.59), ("D3", 146.83), ("D#3", 155.56), 
    ("E3", 164.81), ("F3", 174.61), ("F#3", 185.00), ("G3", 196.00), 
    ("G#3", 207.65), ("A3", 220.00), ("A#3", 233.08), ("B3", 246.94), 
    ("C4", 261.63), ("C#4", 277.18), ("D4", 293.66), ("D#4", 311.13), 
    ("E4", 329.63), ("F4", 349.23), ("F#4", 369.99), ("G4", 392.00), 
    ("G#4", 415.30), ("A4", 440.00), ("A#4", 466.16), ("B4", 493.88), 
    ("C5", 523.25), ("C#5", 554.37), ("D5", 587.33), ("D#5", 622.25), 
    ("E5", 659.26)
]

# Variables
sample_rate = 44100
chunk_size = 8192 
current_pitch = 0

score = 0
frames_held = 0
game_phase = "COUNTDOWN"
end_time = 0
countdown_end_time = 0
game_duration = 60 
current_target_note = random.choice(master_notes)

drawn_x = 640.0

last_ding_time = 0

# Saved
scores_file = "scores.json"
saved_scores = []
if os.path.exists(scores_file):
    with open(scores_file, "r") as file:
        saved_scores = json.load(file)

def detect_pitch_autocorr(audio_data, sample_rate):
    corr = np.correlate(audio_data, audio_data, mode='full')
    corr = corr[len(corr)//2:]
    diff = np.diff(corr)
    try:
        start = np.where(diff > 0)[0][0]
        peak = np.argmax(corr[start:]) + start
        return sample_rate / peak
    except IndexError:
        return 0

def analyze_audio(indata, frames, time, status):
    global current_pitch
    audio_data = indata[:, 0]
    volume = np.max(np.abs(audio_data))
    if volume < 0.05:
        return
    pitch = detect_pitch_autocorr(audio_data, sample_rate)
    if 70 < pitch < 800:
        current_pitch = pitch

# Pygame
pygame.mixer.init()
pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.SCALED)
pygame.display.set_caption("Guitar Training App")
clock = pygame.time.Clock()
pygame.font.init()

# Load sounds
try:
    ding_sound = pygame.mixer.Sound("orb.wav")
    countdown_sound = pygame.mixer.Sound("countdown.wav")
    ending_sound = pygame.mixer.Sound("sol_mi_re_do.wav")
except FileNotFoundError:
    print("Warning: Sound files not found. Game will run silently.")
    ding_sound = countdown_sound = ending_sound = None

# Load image
try:
    bg_image = pygame.image.load("guitar.jpg").convert()
    # Force the image to perfectly fit our 1280x720 window
    bg_image = pygame.transform.scale(bg_image, (1280, 720))
except FileNotFoundError:
    print("Warning: guitar.jpg not found. Using solid background.")
    bg_image = None

large_font = pygame.font.SysFont(None, 100)
medium_font = pygame.font.SysFont(None, 60)
small_font = pygame.font.SysFont(None, 40)

app_state = "MENU"

# Buttons
tuner_btn = pygame.Rect(400, 200, 480, 100)
game_btn = pygame.Rect(400, 350, 480, 100)
scores_btn = pygame.Rect(400, 500, 480, 100)
exit_btn = pygame.Rect(20, 20, 150, 50)

time_15_btn = pygame.Rect(200, 300, 250, 150)
time_30_btn = pygame.Rect(500, 300, 250, 150)
time_60_btn = pygame.Rect(800, 300, 250, 150)

back_btn = pygame.Rect(20, 20, 130, 50) 

is_fullscreen = False
fullscreen_btn = pygame.Rect(1110, 20, 150, 50)

# Main app
with sd.InputStream(channels=1, callback=analyze_audio, blocksize=chunk_size, samplerate=sample_rate):
    while True:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos

                if app_state == "MENU":
                    if tuner_btn.collidepoint(mouse_pos):
                        app_state = "TUNER"
                    elif game_btn.collidepoint(mouse_pos):
                        app_state = "TIME_SELECT" # Go to time selection first!
                    elif scores_btn.collidepoint(mouse_pos):
                        app_state = "SCORES"
                    elif fullscreen_btn.collidepoint(mouse_pos):
                        is_fullscreen = not is_fullscreen 
                        
                        if is_fullscreen:
                            screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN | pygame.SCALED)
                        else:
                            screen = pygame.display.set_mode((1280, 720), pygame.SCALED)
                    elif exit_btn.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                elif app_state == "TIME_SELECT":
                    if back_btn.collidepoint(mouse_pos):
                        app_state = "MENU"

                    elif time_15_btn.collidepoint(mouse_pos):
                        game_duration = 15
                        app_state = "GAME"
                    elif time_30_btn.collidepoint(mouse_pos):
                        game_duration = 30
                        app_state = "GAME"
                    elif time_60_btn.collidepoint(mouse_pos):
                        game_duration = 60
                        app_state = "GAME"
                    
                    if app_state == "GAME":
                        game_phase = "COUNTDOWN"
                        countdown_end_time = current_time + 3000
                        score = 0
                        frames_held = 0
                        current_target_note = random.choice(master_notes)
                        
                        if countdown_sound: 
                            countdown_sound.play()

                elif app_state != "MENU":
                    if back_btn.collidepoint(mouse_pos):
                        app_state = "MENU"

        # screen

        if app_state == "MENU":
            if bg_image:
                screen.blit(bg_image, (0, 0))
            else:
                screen.fill((85, 17, 0))
            pygame.draw.rect(screen, 'blue', tuner_btn, border_radius=15)
            pygame.draw.rect(screen, 'forestgreen', game_btn, border_radius=15)
            pygame.draw.rect(screen, 'purple', scores_btn, border_radius=15)
            pygame.draw.rect(screen, 'gray', fullscreen_btn, border_radius=10)
            pygame.draw.rect(screen, (150, 30, 30), exit_btn, border_radius=15) # Dark Red
            screen.blit(medium_font.render("Exit", True, 'white'), (exit_btn.x + 32, exit_btn.y + 5))
            
            # Change the text based on current state
            if is_fullscreen:
                fs_text = small_font.render("Windowed", True, 'black')
                # Slightly different X coordinate to center the word perfectly
                screen.blit(fs_text, (fullscreen_btn.x + 5, fullscreen_btn.y + 12))
            else:
                fs_text = small_font.render("Fullscreen", True, 'black')
                screen.blit(fs_text, (fullscreen_btn.x + 5, fullscreen_btn.y + 12))
            
            title_text = large_font.render("Guitar Training App", True, 'white')
            screen.blit(title_text, (330, 80))
            eduards_ronalds = small_font.render("Game by Ronalds Ginters and Eduards Ozolins", True, 'white')
            screen.blit(eduards_ronalds, (315, 650))
            
            screen.blit(medium_font.render("Open Tuner", True, 'white'), (tuner_btn.x + 120, tuner_btn.y + 30))
            screen.blit(medium_font.render("Play Game", True, 'white'), (game_btn.x + 130, game_btn.y + 30))
            screen.blit(medium_font.render("High Scores", True, 'white'), (scores_btn.x + 120, scores_btn.y + 30))

        elif app_state == "TIME_SELECT":
            screen.fill((85, 17, 0))
            pygame.draw.rect(screen, 'gray', back_btn, border_radius=10)
            screen.blit(small_font.render("<- Back", True, 'black'), (back_btn.x + 15, back_btn.y + 10))
            
            title = large_font.render("Select Time Limit", True, 'white')
            screen.blit(title, (350, 100))

            pygame.draw.rect(screen, 'teal', time_15_btn, border_radius=20)
            pygame.draw.rect(screen, 'teal', time_30_btn, border_radius=20)
            pygame.draw.rect(screen, 'teal', time_60_btn, border_radius=20)

            screen.blit(large_font.render("15s", True, 'white'), (time_15_btn.x + 70, time_15_btn.y + 40))
            screen.blit(large_font.render("30s", True, 'white'), (time_30_btn.x + 70, time_30_btn.y + 40))
            screen.blit(large_font.render("60s", True, 'white'), (time_60_btn.x + 70, time_60_btn.y + 40))

        elif app_state == "SCORES":
            screen.fill((85, 17, 0))
            # 1. Draw the Back Button
            pygame.draw.rect(screen, 'gray', back_btn, border_radius=10)
            screen.blit(small_font.render("<- Back", True, 'black'), (back_btn.x + 20, back_btn.y + 15))
            
            # --- SECTION: RECENT GAMES (Left Side) ---
            title_recent = large_font.render("Recent Games", True, 'gold')
            screen.blit(title_recent, (150, 80))
            
            y_offset = 200
            if len(saved_scores) == 0:
                screen.blit(medium_font.render("No scores saved yet. Go play!", True, 'white'), (150, 300))
            else:
                for idx, entry in enumerate(reversed(saved_scores[-7:])): 
                    game_date = entry.get("date", "Unknown Date")
                    display_string = f"{game_date}  |  {entry['score']} notes in {entry['time']}s"
                    score_text = medium_font.render(display_string, True, 'white')
                    screen.blit(score_text, (100, y_offset)) 
                    y_offset += 60

            pygame.draw.line(screen, 'gray', (800, 100), (800, 650), 3)

            title_best = large_font.render("Best Scores", True, 'gold')
            screen.blit(title_best, (850, 80))

            best_15 = max([s["score"] for s in saved_scores if s.get("time") == 15], default=0)
            best_30 = max([s["score"] for s in saved_scores if s.get("time") == 30], default=0)
            best_60 = max([s["score"] for s in saved_scores if s.get("time") == 60], default=0)

            screen.blit(medium_font.render("15 Seconds:", True, 'teal'), (850, 200))
            screen.blit(large_font.render(f"{best_15} notes", True, 'white'), (850, 250))

            screen.blit(medium_font.render("30 Seconds:", True, 'teal'), (850, 350))
            screen.blit(large_font.render(f"{best_30} notes", True, 'white'), (850, 400))

            screen.blit(medium_font.render("60 Seconds:", True, 'teal'), (850, 500))
            screen.blit(large_font.render(f"{best_60} notes", True, 'white'), (850, 550))

        elif app_state == "TUNER":
            screen.fill((85, 17, 0))

            pygame.draw.rect(screen, 'gray', back_btn, border_radius=10)
            screen.blit(small_font.render("<- Back", True, 'black'), (back_btn.x + 15, back_btn.y + 10))

            # Calculations
            target_note_name = ""
            target_freq = 0
            smallest_difference = 1000 
            
            if current_pitch > 0:
                for note, freq in guitar_strings.items():
                    diff = abs(current_pitch - freq)
                    if diff < smallest_difference:
                        smallest_difference = diff
                        target_note_name = note
                        target_freq = freq

            # Lerp
            difference = 0
            if current_pitch > 0:
                difference = current_pitch - target_freq
                target_x = 640 + (difference * 6) 
            else:
                target_x = 640 

            drawn_x += (target_x - drawn_x) * 0.10 

            pygame.draw.rect(screen, (130, 130, 135), (340, 100, 600, 500), border_radius=20)
            
            left_led = (60, 20, 20)
            center_led = (20, 60, 20)
            right_led = (60, 20, 20)
            
            if current_pitch > 0:
                if abs(difference) < 1.5:
                    center_led = (0, 255, 0)
                    if (current_time - last_ding_time) > 5000:
                        if ding_sound: 
                            ding_sound.play()
                        last_ding_time = current_time
                elif difference <= -1.5:
                    left_led = (255, 0, 0)
                elif difference >= 1.5:
                    right_led = (255, 0, 0)
                    has_played_ding = False
            else:
                has_played_ding = False

            pygame.draw.circle(screen, left_led, (540, 150), 15)
            pygame.draw.circle(screen, center_led, (640, 150), 15)
            pygame.draw.circle(screen, right_led, (740, 150), 15)
            
            screen.blit(small_font.render("b", True, 'black'), (535, 175))
            pygame.draw.polygon(screen, 'black', [(640, 175), (635, 185), (645, 185)])
            screen.blit(small_font.render("#", True, 'black'), (735, 175))

            lcd_rect = pygame.Rect(380, 220, 520, 340)
            pygame.draw.rect(screen, (140, 160, 140), lcd_rect, border_radius=10) 
            pygame.draw.rect(screen, (50, 60, 50), lcd_rect, 4, border_radius=10) # Border

            screen.blit(small_font.render("GUITAR", True, (50, 60, 50)), (400, 240))
            screen.blit(small_font.render("AUTO 440", True, (50, 60, 50)), (740, 240))
            
            pygame.draw.polygon(screen, (50, 60, 50), [(640, 280), (635, 270), (645, 270)])
            
            if current_pitch > 0:
                stop_x = max(400, min(880, drawn_x))
                
                pygame.draw.line(screen, (30, 30, 30), (640, 550), (int(stop_x), 300), 6)
                
                note_text = large_font.render(target_note_name, True, (30, 30, 30))
                screen.blit(note_text, (600, 400))
                
                hz_text = small_font.render(f"{current_pitch:.1f} Hz", True, (50, 60, 50))
                screen.blit(hz_text, (750, 500))
            else:
                prompt = medium_font.render("Pluck string...", True, (100, 110, 100))
                screen.blit(prompt, (500, 400))
        elif app_state == "GAME":
            screen.fill((85, 17, 0))
            pygame.draw.rect(screen, 'gray', back_btn, border_radius=10)
            screen.blit(small_font.render("<- Back", True, 'black'), (back_btn.x + 20, back_btn.y + 15))
            
            if game_phase == "COUNTDOWN":
                time_left = (countdown_end_time - current_time) / 1000
                current_second = int(time_left) + 1
                
                if time_left > 0:
                    screen.blit(large_font.render(str(current_second), True, 'white'), (620, 350))
                    screen.blit(medium_font.render("Get Ready...", True, 'gold'), (530, 250))
                    
                else:
                    game_phase = "PLAYING"
                    end_time = current_time + (game_duration * 1000) 
                    last_tick_second = 3

            elif game_phase == "PLAYING":
                if current_time < end_time:
                    target_freq = current_target_note[1]
                    
                    pitch_difference = abs(current_pitch - target_freq)

                    if pitch_difference < 3.0 and current_pitch > 0:
                        frames_held += 1  
                        if frames_held >= 10:
                            score += 1
                            current_target_note = random.choice(master_notes)
                            frames_held = 0 
                    elif current_pitch > 0:
                        frames_held = 0

                    # Lerp
                    if current_pitch > 0:
                        target_x = 640 + ((current_pitch - target_freq) * 15) 
                    else:
                        target_x = 640 

                    drawn_x += (target_x - drawn_x) * 0.15 


                    time_left_ms = end_time - current_time
                    time_percentage = time_left_ms / (game_duration * 1000)
                    
                    bar_max_width = 400
                    current_bar_width = int(bar_max_width * time_percentage)
                    
                    if time_percentage > 0.5:
                        bar_color = 'green'     
                    elif time_percentage > 0.2:
                        bar_color = 'yellow'    
                    else:
                        bar_color = 'red'       

                    pygame.draw.circle(screen, 'blue', (int(drawn_x), 360), 100)
                    
                    screen.blit(large_font.render(current_target_note[0], True, 'white'), (600, 120))
                    screen.blit(small_font.render(f"Score: {score}", True, 'green'), (50, 150))       
                    
                    pygame.draw.rect(screen, 'gray', (440, 50, bar_max_width, 30), border_radius=15)
                    pygame.draw.rect(screen, bar_color, (440, 50, max(0, current_bar_width), 30), border_radius=15)
                    
                else:
                    if ending_sound: ending_sound.play()
                    game_phase = "GAME_OVER"
                    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
                    new_score_entry = {
                        "date": timestamp, 
                        "time": game_duration, 
                        "score": score
                    }
                    saved_scores.append(new_score_entry)
                    with open(scores_file, "w") as file:
                        json.dump(saved_scores, file, indent=4)      

            elif game_phase == "GAME_OVER":
                screen.blit(large_font.render("Time's Up!", True, 'white'), (450, 250))
                screen.blit(large_font.render(f"Final Score: {score} notes", True, 'gold'), (310, 350))

        pygame.display.flip()
        clock.tick(60)
