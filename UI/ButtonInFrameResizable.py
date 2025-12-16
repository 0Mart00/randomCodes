from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector2, loadPrcFileData
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task

# --- KONFIGURÁCIÓ ---
WINDOW_SIZE = 750
FRAME_SIZE = 500
RESIZE_TOLERANCE = 0.05 

TARGET_FRAME_TEXT_SCALE = 0.07  

# --- SKÁLÁZÁSI PARAMÉTEREK ---
BUTTON_BASE_HALF_SIZE = 0.1  # A gomb alap mérete (0.1 -> width 0.2)
INTERNAL_BUTTON_FRACTION = 0.8 # A Frame hány százalékát töltse ki a gomb
# --------------------

prc_data = f"""
window-title Dinamikus Gomb Méret (setScale() Használatával)
win-size {WINDOW_SIZE} {WINDOW_SIZE}
"""
loadPrcFileData("", prc_data)


class ManualFrameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self) 
        self.is_dragging = False
        self.is_resizing = False 
        self.drag_offset = LVector2(0, 0) 
        self.active_frame = None 
        self.resizing_corner = None
        self.internal_button = None
        self.frame_list = []
        
        self._setup_panels()
        self._setup_drag_events() 

    def _internal_button_click(self):
        self.status_text.setText("Belső Gomb Megnyomva!")

    def _internal_button_stop_event(self, event):
        # Megakadályozza, hogy a gombnyomás átmenjen a frame-re (drag start)
        return event.stop()
        
    def _setup_panels(self):
        self.status_text = OnscreenText(
            text="Húzd a Frame-et, vagy fogd meg a sarkát a méretezéshez!",
            pos=(0, 0.9), 
            scale=0.07,   
            fg=(1, 1, 1, 1), 
            mayChange=True
        )
        
        panel_half_scale = FRAME_SIZE / WINDOW_SIZE / 2 
        initial_width = panel_half_scale * 2
        initial_height = panel_half_scale * 2
        
        # --- FRAME 1 (Kék - Ezen van a gomb) ---
        frame1 = DirectFrame(
            frameColor=(0.1, 0.1, 0.8, 0.9),
            frameSize=(-panel_half_scale, panel_half_scale, -panel_half_scale, panel_half_scale),
            pos=(-0.2, 0, -0.2), 
            text="Frame 1\n(Skálázós)", 
            text_scale=0.05, 
            text_pos=(0, 0.25)
        )
        self.frame_list.append(frame1)

        # --- BELSŐ GOMB (FIX ALAPMÉRET, DINAMIKUS SCALE) ---
        self.internal_button = DirectButton(
            parent=frame1, 
            frameColor=(0.1, 0.8, 0.1, 1),
            # Fix alapméretet adunk neki, nem állítgatjuk a frameSize-t később!
            frameSize=(-BUTTON_BASE_HALF_SIZE, BUTTON_BASE_HALF_SIZE, 
                       -BUTTON_BASE_HALF_SIZE, BUTTON_BASE_HALF_SIZE), 
            pos=(0, 0, 0), 
            text="Auto Gomb",
            command=self._internal_button_click,
            scale=(1, 1, 1) # Kezdő skála
        )
        self.internal_button.bind('press', self._internal_button_stop_event)
        
        # Kezdő skála beállítása
        self._update_button_scale(width=initial_width, height=initial_height)
        
        # --- FRAME 2 (Narancs - Csak hogy legyen másik is) ---
        frame2 = DirectFrame(
            frameColor=(0.8, 0.5, 0.1, 0.9), 
            frameSize=(-panel_half_scale, panel_half_scale, -panel_half_scale, panel_half_scale),
            pos=(0.3, 0, 0.3), 
            text="Frame 2", 
            text_scale=0.1
        )
        self.frame_list.append(frame2)
        
    def _check_interaction_area(self, mouse_x_norm, mouse_y_norm, frame):
        """Megnézi, hogy a kurzor a frame felett, vagy a szélein van-e."""
        frame_pos = frame.getPos()
        frame_center_x = frame_pos.getX()
        frame_center_y = frame_pos.getZ()
        
        min_x_size, max_x_size, min_y_size, max_y_size = frame['frameSize']
        
        min_x_abs = frame_center_x + min_x_size
        max_x_abs = frame_center_x + max_x_size
        min_y_abs = frame_center_y + min_y_size
        max_y_abs = frame_center_y + max_y_size
        
        tolerance = RESIZE_TOLERANCE 
        
        is_inside = (min_x_abs <= mouse_x_norm <= max_x_abs and 
                     min_y_abs <= mouse_y_norm <= max_y_abs)

        if not is_inside: return None, None
            
        is_right = (max_x_abs - tolerance) < mouse_x_norm < (max_x_abs + tolerance)
        is_left  = (min_x_abs - tolerance) < mouse_x_norm < (min_x_abs + tolerance)
        is_top   = (max_y_abs - tolerance) < mouse_y_norm < (max_y_abs + tolerance)
        is_bottom= (min_y_abs - tolerance) < mouse_y_norm < (min_y_abs + tolerance) 
        
        corner = None
        if is_right and is_top: corner = 'tr'
        elif is_left and is_top: corner = 'tl'
        elif is_right and is_bottom: corner = 'br'
        elif is_left and is_bottom: corner = 'bl'
        
        if corner: return 'resize', corner
            
        return 'drag', None

    def start_interaction_check(self):
        if not base.mouseWatcherNode.hasMouse(): return
        mouse_norm = base.mouseWatcherNode.getMouse()
        mouse_x = mouse_norm.getX()
        mouse_y = mouse_norm.getY()
        
        self.is_dragging = False
        self.is_resizing = False
        self.active_frame = None

        # Fordított sorrendben ellenőrizzük (felül lévő van elől)
        for frame in reversed(self.frame_list):
            action, corner = self._check_interaction_area(mouse_x, mouse_y, frame)
            
            if action:
                self.active_frame = frame
                
                # Frame előre hozása (lista végére + reparent)
                self.frame_list.remove(frame)
                self.frame_list.append(frame)
                frame.reparentTo(base.aspect2d)
                
                if action == 'resize':
                    self.is_resizing = True
                    self.resizing_corner = corner
                    self.active_frame['frameColor'] = (0.8, 0.1, 0.8, 0.9) # Lila = resize
                        
                elif action == 'drag':
                    self.is_dragging = True
                    frame_pos = frame.getPos()
                    self.drag_offset = LVector2(frame_pos.getX() - mouse_x, frame_pos.getZ() - mouse_y)
                    self.active_frame['frameColor'] = (0.0, 0.8, 0.0, 0.9) # Zöld = drag
                
                self.status_text.setText(f"{'MÉRETEZÉS' if self.is_resizing else 'HÚZÁS'}")
                
                # Frissítsük a gombot azonnal kattintáskor is (ha ez a gombos frame)
                if self.internal_button and self.internal_button.getParent() == frame:
                    current_size = frame['frameSize']
                    w = current_size[1] - current_size[0]
                    h = current_size[3] - current_size[2]
                    self._update_button_scale(w, h)

                return 

        self.status_text.setText("ÜRES TERÜLET")
        self.taskMgr.doMethodLater(1.5, self.reset_status_text, 'reset_task')

    def _setup_drag_events(self):
        self.accept('mouse1', self.start_interaction_check) 
        self.accept('mouse1-up', self.stop_interaction)
        self.taskMgr.add(self.interaction_task, 'interaction_task')


    def interaction_task(self, task):
        if not self.active_frame or not base.mouseWatcherNode.hasMouse():
            return Task.cont
            
        mouse_norm = base.mouseWatcherNode.getMouse()
        mouse_x = mouse_norm.getX()
        mouse_y = mouse_norm.getY()
        frame = self.active_frame
        
        if self.is_dragging:
            new_x = mouse_x + self.drag_offset.getX()
            new_y = mouse_y + self.drag_offset.getY()
            frame.setPos(new_x, 0, new_y)
            
        elif self.is_resizing:
            current_x, current_y = frame.getX(), frame.getZ()
            min_x_size, max_x_size, min_y_size, max_y_size = frame['frameSize']
            
            # Jelenlegi határok abszolút pozíciója
            min_x_abs = current_x + min_x_size
            max_x_abs = current_x + max_x_size
            min_y_abs = current_y + min_y_size
            max_y_abs = current_y + max_y_size
            
            # Sarok szerinti új határok
            if 'r' in self.resizing_corner: max_x_abs = mouse_x
            elif 'l' in self.resizing_corner: min_x_abs = mouse_x
            
            if 't' in self.resizing_corner: max_y_abs = mouse_y
            elif 'b' in self.resizing_corner: min_y_abs = mouse_y
            
            # Új méret számítása (minimum 0.05)
            width = max(0.05, max_x_abs - min_x_abs)
            height = max(0.05, max_y_abs - min_y_abs)

            # Frame frissítése (bounds és pozíció)
            frame['frameSize'] = (-width / 2, width / 2, -height / 2, height / 2)
            new_center_x = min_x_abs + width / 2
            new_center_y = min_y_abs + height / 2
            frame.setPos(new_center_x, 0, new_center_y)
            
            # --- ITT TÖRTÉNIK A VARÁZSLAT ---
            # Ha ez a gombos frame, frissítjük a gomb skáláját
            if self.internal_button and self.internal_button.getParent() == frame:
                self._update_button_scale(width, height)
            
            self.status_text.setText(f"MÉRETEZÉS: W:{width:.2f}, H:{height:.2f}")

        return Task.cont

    def _update_button_scale(self, width, height):
        """
        Kiszámolja a gomb NodePath SCALE értékeit.
        A 'width' és 'height' a szülő Frame aktuális teljes szélessége/magassága.
        """
        if not self.internal_button:
            return

        # 1. Mennyi legyen a gomb mérete a képernyőn? (A Frame 80%-a)
        target_width = width * INTERNAL_BUTTON_FRACTION
        target_height = height * INTERNAL_BUTTON_FRACTION
        
        # 2. Mekkora a gomb alap definíciója? (frameSize paraméterből)
        # (-0.1 -től 0.1-ig = 0.2 egység széles)
        base_width = BUTTON_BASE_HALF_SIZE * 2
        base_height = BUTTON_BASE_HALF_SIZE * 2
        
        # 3. Kiszámoljuk a torzítási arányt (Scale Factor)
        # Ez az, amit kértél: a scale változik, nem a frameSize!
        scale_x = target_width / base_width
        scale_y = target_height / base_height
        
        # 4. Beállítjuk a NodePath skáláját
        self.internal_button.setScale(scale_x, 1, scale_y) 

        # 5. [EXTRA] Szöveg torzulás korrigálása
        # Ha a gombot 5x szélesebbre húzzuk (scale_x=5), a betűk is 5x szélesek lennének.
        # Ezt úgy javítjuk, hogy a szöveg skáláját elosztjuk a gomb skálájával.
        
        # Kívánt vizuális méret (hogy mindig ekkora maradjon a betű):
        visual_size = TARGET_FRAME_TEXT_SCALE 
        
        # Matek: (GombScale) * (TextScale) = (VisualSize)
        # Tehát: TextScale = VisualSize / GombScale
        ts_x = visual_size / scale_x
        ts_y = visual_size / scale_y
        
        # Tuple-t adunk át, így külön skálázza X és Y irányban a szöveget
        self.internal_button['text_scale'] = (ts_x, ts_y)

    def stop_interaction(self):
        if self.active_frame:
            # Szín visszaállítása
            is_frame1 = (self.internal_button and self.internal_button.getParent() == self.active_frame)
            if is_frame1:
                 self.active_frame['frameColor'] = (0.1, 0.1, 0.8, 0.9)
            else:
                 self.active_frame['frameColor'] = (0.8, 0.5, 0.1, 0.9)
            
            self.is_dragging = False
            self.is_resizing = False
            self.active_frame = None
            self.resizing_corner = None
            self.taskMgr.doMethodLater(1.5, self.reset_status_text, 'reset_task')
        
        else:
            self.taskMgr.doMethodLater(1.5, self.reset_status_text, 'reset_task')


    def reset_status_text(self, task):
        self.status_text.setText("Húzd a Frame-et, vagy fogd meg a sarkát a méretezéshez!")
        return task.done
    
if __name__ == '__main__':
    app = ManualFrameApp()
    app.run()