from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, LVector2, loadPrcFileData
from direct.gui.DirectFrame import DirectFrame  # <-- DirectFrame használata
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from direct.showbase.DirectObject import DirectObject

# 1. Konstansok beállítása
WINDOW_SIZE = 750
FRAME_SIZE = 500
# Tűréshatár a sarok/szél érzékeléséhez (normált koordinátában)
RESIZE_TOLERANCE = 0.05 

# --- GLOBÁLIS KONFIGURÁCIÓ ---
prc_data = f"""
window-title Két Frame Kézi Koordináta Ellenőrzéssel
win-size {WINDOW_SIZE} {WINDOW_SIZE}
"""
loadPrcFileData("", prc_data)


# --- FŐ OSZTÁLY ---

class ManualFrameApp(ShowBase):
    def __init__(self):
        
        ShowBase.__init__(self) 

        # 2. Állapotok beállítása
        self.is_dragging = False
        self.is_resizing = False 
        self.drag_offset = LVector2(0, 0) 
        self.active_frame = None 
        self.resizing_corner = None
        
        # 3. Két Frame Létrehozása
        self.frame_list = []
        self._setup_panels()
        
        # 4. Események regisztrálása
        self._setup_drag_events()


    def _setup_panels(self):
        """Létrehozza a két DirectFrame-et."""
        
        self.status_text = OnscreenText(
            text="Kattints a Frame-ekre!",
            pos=(0, 0.9), 
            scale=0.07,   
            fg=(1, 1, 1, 1), 
            mayChange=True
        )
        
        panel_width_scale = FRAME_SIZE / WINDOW_SIZE
        
        # FRAME 1 (Kék)
        frame1 = DirectFrame(
            frameColor=(0.1, 0.1, 0.8, 0.9),
            frameSize=(-panel_width_scale, panel_width_scale, -panel_width_scale, panel_width_scale),
            pos=(-0.2, 0, -0.2), 
            text="Frame 1 - Kék", 
            text_scale=0.1
        )
        self.frame_list.append(frame1)

        # FRAME 2 (Narancs)
        frame2 = DirectFrame(
            frameColor=(0.8, 0.5, 0.1, 0.9), 
            frameSize=(-panel_width_scale, panel_width_scale, -panel_width_scale, panel_width_scale),
            pos=(0.3, 0, 0.3), 
            text="Frame 2 - Narancs", 
            text_scale=0.1
        )
        self.frame_list.append(frame2)
        
    def _check_interaction_area(self, mouse_x_norm, mouse_y_norm, frame):
        """
        Kézi ellenőrzés: Megállapítja, hogy a kattintás a húzási vagy méretezési zónában van-e.
        Visszaadja: ('resize', 'tr') vagy ('drag', None) vagy (None, None).
        """
        frame_pos = frame.getPos()
        frame_center_x = frame_pos.getX()
        frame_center_y = frame_pos.getZ()
        
        # Frame aktuális határainak kiszámítása
        min_x_size, max_x_size, min_y_size, max_y_size = frame['frameSize']
        min_x_abs = frame_center_x + min_x_size
        max_x_abs = frame_center_x + max_x_size
        min_y_abs = frame_center_y + min_y_size
        max_y_abs = frame_center_y + max_y_size
        
        tolerance = RESIZE_TOLERANCE 
        
        # 1. Ellenőrizzük, a kattintás a Frame területén belül van-e
        is_inside = (min_x_abs <= mouse_x_norm <= max_x_abs and 
                     min_y_abs <= mouse_y_norm <= max_y_abs)

        if not is_inside:
            return None, None # Nincs a Frame-en belül
            
        # 2. Ellenőrizzük, a sarok zónában van-e (Méretezés)
        is_right = (max_x_abs - tolerance) < mouse_x_norm < (max_x_abs + tolerance)
        is_left  = (min_x_abs - tolerance) < mouse_x_norm < (min_x_abs + tolerance)
        is_top   = (max_y_abs - tolerance) < mouse_y_norm < (max_y_abs + tolerance)
        is_bottom= (min_y_abs - tolerance) < mouse_y_norm < (min_y_abs + tolerance)
        
        corner = None
        if is_right and is_top: corner = 'tr'
        elif is_left and is_top: corner = 'tl'
        elif is_right and is_bottom: corner = 'br'
        elif is_left and is_bottom: corner = 'bl'
        
        if corner:
            return 'resize', corner
            
        # 3. Ha a Frame-en belül van, de nem a sarokban (Húzás)
        return 'drag', None


    def start_interaction_check(self):
        """Globális 'mouse1' eseményre fut le. Kézzel ellenőrzi az interakció típusát."""
        if not base.mouseWatcherNode.hasMouse():
            return
            
        mouse_norm = base.mouseWatcherNode.getMouse()
        mouse_x = mouse_norm.getX()
        mouse_y = mouse_norm.getY()
        
        # Állapotok alaphelyzetbe állítása minden kattintásnál
        self.is_dragging = False
        self.is_resizing = False
        self.active_frame = None

        # Fordított sorrendben ellenőrizzük (hogy a felül lévő Frame kapjon prioritást)
        for frame in reversed(self.frame_list):
            
            action, corner = self._check_interaction_area(mouse_x, mouse_y, frame)
            
            if action:
                # --- Interakció kezdete ---
                self.active_frame = frame
                frame_pos = frame.getPos()
                frame_center_x = frame_pos.getX()
                frame_center_y = frame_pos.getZ()
                
                if action == 'resize':
                    self.is_resizing = True
                    self.resizing_corner = corner
                    self.status_text.setText(f"MÉRETEZÉS ({frame.node().getName()} - {corner})")
                    self.active_frame['frameColor'] = (0.8, 0.1, 0.8, 0.9) # Lila
                    
                elif action == 'drag':
                    self.is_dragging = True
                    self.status_text.setText(f"HÚZÁS ({frame.node().getName()})")
                    
                    self.drag_offset = LVector2(
                        frame_center_x - mouse_x,
                        frame_center_y - mouse_y
                    )
                    self.active_frame['frameColor'] = (0.0, 0.8, 0.0, 0.9) # Zöld
                
                # Z-sorrend frissítése: a húzott Frame kerül felülre
                self.frame_list.remove(frame)
                self.frame_list.append(frame)
                frame.reparentTo(base.aspect2d)

                return # Aktív Frame-et találtunk, befejezzük az ellenőrzést

        # Ha a ciklus lefutott: NEM BELEKATTINTOTT
        self.status_text.setText("NEM BELEKATTINTOTT (Kívül)")
        self.taskMgr.doMethodLater(1.5, self.reset_status_text, 'reset_task')


    # --- DRAG ÉS RESIZE LOGIKA ---

    def _setup_drag_events(self):
        # A start_interaction_check váltja ki az egér lenyomására
        self.accept('mouse1', self.start_interaction_check) 
        self.accept('mouse1-up', self.stop_interaction)
        self.taskMgr.add(self.interaction_task, 'interaction_task')

    def interaction_task(self, task):
        """Folyamatosan frissíti a pozíciót vagy a méretet."""
        if not self.active_frame or not base.mouseWatcherNode.hasMouse():
            return Task.cont
            
        mouse_norm = base.mouseWatcherNode.getMouse()
        mouse_x = mouse_norm.getX()
        mouse_y = mouse_norm.getY()
        frame = self.active_frame
        
        if self.is_dragging:
            # --- HÚZÁS ---
            new_x = mouse_x + self.drag_offset.getX()
            new_y = mouse_y + self.drag_offset.getY()
            frame.setPos(new_x, 0, new_y)
            
        elif self.is_resizing:
            # --- MÉRETEZÉS ---
            current_x, current_y = frame.getX(), frame.getZ()
            min_x_size, max_x_size, min_y_size, max_y_size = frame['frameSize']
            
            min_x_abs = current_x + min_x_size
            max_x_abs = current_x + max_x_size
            min_y_abs = current_y + min_y_size
            max_y_abs = current_y + max_y_size
            
            new_min_x_abs, new_max_x_abs, new_min_y_abs, new_max_y_abs = min_x_abs, max_x_abs, min_y_abs, max_y_abs

            # Pozíciók frissítése a kurzorhoz
            if 'r' in self.resizing_corner: new_max_x_abs = mouse_x
            elif 'l' in self.resizing_corner: new_min_x_abs = mouse_x
            
            if 't' in self.resizing_corner: new_max_y_abs = mouse_y
            elif 'b' in self.resizing_corner: new_min_y_abs = mouse_y
                
            # Szélesség és magasság számítása (minimum méret biztosítása)
            width = max(0.05, new_max_x_abs - new_min_x_abs)
            height = max(0.05, new_max_y_abs - new_min_y_abs)

            # Új Frame méret beállítása a centerhez képest
            frame['frameSize'] = (
                -width / 2, width / 2,
                -height / 2, height / 2
            )
            
            # Pozíció korrekciója (a Frame középpontja is eltolódik)
            new_center_x = new_min_x_abs + width / 2
            new_center_y = new_min_y_abs + height / 2
            
            frame.setPos(new_center_x, 0, new_center_y)
            
            self.status_text.setText(f"MÉRETEZÉS: W:{width:.2f}, H:{height:.2f}")

        return Task.cont


    def stop_interaction(self):
        """Leállítja a húzást vagy a méretezést."""
        if self.active_frame:
            
            # Szín visszaállítása
            if self.active_frame.node().getName().endswith("Kék"):
                self.active_frame['frameColor'] = (0.1, 0.1, 0.8, 0.9)
            else:
                self.active_frame['frameColor'] = (0.8, 0.5, 0.1, 0.9)
            
            self.is_dragging = False
            self.is_resizing = False
            self.active_frame = None
            self.resizing_corner = None
            self.taskMgr.doMethodLater(1.5, self.reset_status_text, 'reset_task')

    def reset_status_text(self, task):
        """Visszaállítja a státusz szöveget."""
        self.status_text.setText("Húzd a Frame-et, vagy fogd meg a sarkát a méretezéshez!")
        return task.done
    
    def on_window_resize(self, window):
        pass

# Az alkalmazás futtatása
app = ManualFrameApp()
app.run()