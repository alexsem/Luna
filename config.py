import pygame_gui

import os
from dotenv import load_dotenv

load_dotenv()

SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", 600))
SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", 480))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 10))
FACE_WIDTH = 250
CHAT_AREA_X = FACE_WIDTH + 20

def initialize(pygame, pygame_gui):
    # --- 1. CONFIGURACIÓN INICIAL Y PYGAME ---
    pygame.init()

    screen_width = SCREEN_WIDTH
    screen_height = SCREEN_HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)

    pygame.display.set_caption("Assitant - Luna")

    # Creamos un reloj para pygame_gui
    clock = pygame.time.Clock()

    chat_history = []

    # --- 2. CARGAR ROSTROS ---
    # Ya no necesitamos la variable 'font' fuera de esta función, pygame_gui la gestiona

    face_neutral = pygame.image.load("faces/neutral.png").convert_alpha()
    face_happy = pygame.image.load("faces/happy.png").convert_alpha()
    face_sad = pygame.image.load("faces/sad.png").convert_alpha()

    face_width = 250
    face_height = 250

    face_neutral = pygame.transform.smoothscale(face_neutral, (face_width, face_height))
    face_happy = pygame.transform.smoothscale(face_happy, (face_width, face_height))
    face_sad = pygame.transform.smoothscale(face_sad, (face_width, face_height))

    faces = {
        "neutral": face_neutral,
        "happy": face_happy,
        "sad": face_sad,
    }

    current_mood = "neutral"

    # --- 3. CONFIGURACIÓN DE PYGAME_GUI ---

    # El Manager gestiona todos los elementos de la GUI
    manager = pygame_gui.UIManager((screen_width, screen_height))

    # Definición de coordenadas y dimensiones del área de chat
    CHAT_AREA_X = face_width + 20
    CHAT_AREA_WIDTH = screen_width - CHAT_AREA_X - 10

    # 4. Crear la Caja de Texto de Chat (UITextBox)
    chat_rect = pygame.Rect(CHAT_AREA_X, 10, CHAT_AREA_WIDTH, screen_height - 60)
    chat_text_box = pygame_gui.elements.UITextBox(
        html_text="",  # Empezamos con el texto vacío
        relative_rect=chat_rect,
        manager=manager,
        object_id='#chat_log'  # ID útil para temas (themes)
    )

    # 5. Crear la Entrada de Texto (UITextEntryLine)
    input_rect = pygame.Rect(CHAT_AREA_X, screen_height - 40, CHAT_AREA_WIDTH, 30)
    input_text_entry = pygame_gui.elements.UITextEntryLine(
        relative_rect=input_rect,
        manager=manager,
        object_id='#input_box'
    )
    input_text_entry.set_text("Write: ")
    input_text_entry.focus()  # Enfocar el cursor al inicio

    # --- 6. RETORNO DE VARIABLES ---
    # Eliminamos 'font', 'response_text', y 'user_input' de los retornos
    # y añadimos los componentes de pygame_gui.
    return (
        screen,
        faces,
        current_mood,
        chat_history,
        manager,
        clock,
        input_text_entry,
        chat_text_box
    )
