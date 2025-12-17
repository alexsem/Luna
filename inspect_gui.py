
import pygame
import pygame_gui
from pygame_gui.elements import UITextBox

pygame.init()
window_surface = pygame.display.set_mode((800, 600))
manager = pygame_gui.UIManager((800, 600))

text_box = UITextBox(
    html_text="<br>" * 100 + "Bottom",
    relative_rect=pygame.Rect(0, 0, 200, 200),
    manager=manager
)

print("Attributes of UITextBox:")
for attr in dir(text_box):
    if "scroll" in attr:
        print(f" -> {attr}")

if hasattr(text_box, "scroll_bar"):
    print("Has 'scroll_bar'")
    sb = text_box.scroll_bar
    if sb:
        print(f"Has start_percentage: {hasattr(sb, 'start_percentage')}")
        print(f"Has set_scroll_from_start_percentage: {hasattr(sb, 'set_scroll_from_start_percentage')}")
        print(f"Has scroll_position: {hasattr(sb, 'scroll_position')}")
        print(f"Has bottom_limit: {hasattr(sb, 'bottom_limit')}")

    
print("TextBox 'append' methods:")
for attr in dir(text_box):
    if "append" in attr:
        print(f" -> {attr}")
