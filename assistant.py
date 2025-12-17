import pygame
import pygame_gui
import pytest
import sys
from config import initialize
from general_functions import *

# --- STARTUP TESTS ---
print("Running startup tests...")
retcode = pytest.main(["-q", "tests/test_sentiment.py"])
if retcode == 0:
    print("All tests passed")
else:
    print(f"Startup tests FAILED with code {retcode}")
    # Optional: Decide if we want to blocking exit or continue
    # For now, we just warn and continue as per request "throw a message"
    
screen, faces, current_mood, chat_history, manager, clock, input_text_entry, chat_text_box = initialize(pygame, pygame_gui)

# Startup Connection Check
if not check_ollama_connection():
    chat_history.append({'type': 'ia', 'text': "**[SYSTEM WARNING]: Cannot connect to Ollama. Make sure it is running.**"})
    update_chat_box(chat_text_box, chat_history)
    # scroll_pending is initialized below, but we haven't started loop yet. 
    # It will just stay at top which is fine for first message or we can assume it fits.

response_generator = None
scroll_hold = 0

# --- UI ELEMENTS EXTRA ---
# Stop Button
# We need to shrink the input box to make room for the Stop button on the same line
FACE_WIDTH = 250
CHAT_AREA_X = FACE_WIDTH + 20
current_w = screen.get_width()
current_h = screen.get_height()
available_width = current_w - CHAT_AREA_X - 10
stop_btn_width = 80
start_stop_btn_x = current_w - stop_btn_width - 10
input_width = start_stop_btn_x - CHAT_AREA_X - 10

# Resize existing input entry
input_text_entry.set_dimensions((input_width, 30))
# Position is already correct y-wise, but width changed.

stop_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect(start_stop_btn_x, current_h - 40, stop_btn_width, 30),
    text='Stop',
    manager=manager
)
# We can use anchors to keep it valid on resize! 
# But we also need to update the chat box and input box manually if anchors aren't set on them.
# config.py initialized them without anchors (likely). We might need to handle resize manually or update config.py?
# Let's retro-fit anchors to existing elements if possible, or just resize manually.
# Accessing private props or just verify config.py?
# config.py created them. let's check config.py again... 
# They did not have anchors. We will handle resize manually for simplicity in this script.

running = True
while running:
    time_delta = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.VIDEORESIZE:
            try:
                # Update the manager's size
                manager.set_window_resolution((event.w, event.h))
                
                # Recalculate layout
                FACE_WIDTH = 250
                CHAT_AREA_X = FACE_WIDTH + 20
                
                # Ensure minimum dimensions for layout calculations to avoid negative Rects
                # If the window is smaller than these, content will be clipped/hidden but app won't crash
                layout_width = max(event.w, CHAT_AREA_X + 50) 
                layout_height = max(event.h, 200)
                
                chat_width = layout_width - CHAT_AREA_X - 10
                
                # Update Chat Text Box
                chat_text_box.set_relative_position((CHAT_AREA_X, 10))
                chat_text_box.set_dimensions((chat_width, layout_height - 60))
                
                # Layout for Input Row (Input + Stop Button)
                stop_btn_width = 80
                gap = 10
                # Available width for input row matches chat_width (which goes up to right margin)
                # But we want button on the right.
                
                # New Input Width
                input_new_width = chat_width - stop_btn_width - gap
                
                # Update Input
                input_text_entry.set_relative_position((CHAT_AREA_X, layout_height - 40))
                input_text_entry.set_dimensions((input_new_width, 30))
                
                # Update Stop Button
                btn_x = CHAT_AREA_X + input_new_width + gap
                stop_button.set_relative_position((btn_x, layout_height - 40))
                stop_button.set_dimensions((stop_btn_width, 30))
                
            except Exception as e:
                print(f"CRITICAL ERROR during resize: {e}")
                # Optional: log to chat history so user sees it in the app if it survives
                # chat_history.append({'type': 'ia', 'text': f"\n[SYSTEM ERROR]: Resize failed: {e}"})
                # update_chat_box(chat_text_box, chat_history)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == stop_button:
                if response_generator:
                    response_generator.stop()
                    response_generator = None
                    chat_history[-1]['text'] += " **[STOPPED]**"
                    update_chat_box(chat_text_box, chat_history)
                    scroll_hold = 5

        # Capture the text input event from the GUI widget
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_element == input_text_entry:
            user_input = input_text_entry.get_text().strip()

            if user_input:
                # 1. Add user message to history and chat box
                chat_history.append({'type': 'user', 'text': user_input})
                update_chat_box(chat_text_box, chat_history)  # New function to update the widget
                scroll_hold = 5

                # 2. Start the streaming process (Threaded)
                response_generator = ThreadedGenerator(user_input, chat_history)

                # 3. Add IA placeholder
                chat_history.append({'type': 'ia', 'text': ''})

                # Clear the input box and set focus back
                input_text_entry.set_text("")
                input_text_entry.focus()

        # IMPORTANT: Pass ALL events to the UIManager
        manager.process_events(event)

    if response_generator:
        # Loop to consume all available chunks in the queue without blocking
        while True:
            item = response_generator.get_chunk()
            if item is None:
                break
                
            msg_type, content = item
            
            if msg_type == "data":
                # Append content to the last message (IA)
                chat_history[-1]['text'] += content
                update_chat_box(chat_text_box, chat_history)
                scroll_hold = 5
                
            elif msg_type == "done":
                # Generation finished
                final_text = chat_history[-1]['text']
                current_mood = get_mood_from_text(final_text)
                update_chat_box(chat_text_box, chat_history)
                scroll_hold = 5
                response_generator = None
                break
                
            elif msg_type == "error":
                chat_history[-1]['text'] += f"\n[ERROR: {content}]"
                update_chat_box(chat_text_box, chat_history)
                scroll_hold = 5
                response_generator = None
                break

    manager.update(time_delta)
    
    if scroll_hold > 0:
        # Check if scrollbar exists and is valid
        if getattr(chat_text_box, "scroll_bar", None) is not None:
             chat_text_box.scroll_bar.scroll_position = chat_text_box.scroll_bar.bottom_limit
             chat_text_box.scroll_bar.start_percentage = 1.0
        scroll_hold -= 1

    screen.fill((0, 0, 0))

    # DIBUJAR ROSTRO (Lado izquierdo - Custom Drawing)
    FACE_WIDTH = 250
    face_rect = faces[current_mood].get_rect()
    face_rect.center = (FACE_WIDTH / 2, screen.get_height() / 2 - 50)
    screen.blit(faces[current_mood], face_rect)

    # Draw all GUI elements (chat box, input box)
    manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()
