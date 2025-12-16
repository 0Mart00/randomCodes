from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, LVector2
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task

class DragApp(ShowBase):
    def __init__(self):
        # ShowBase inicializálása
        ShowBase.__init__(self)

        # 1. Konstansok beállítása
        self.WINDOW_SIZE = 750
        self.FRAME_SIZE = 500
        
        # Állapotjelzők húzáshoz
        self.is_dragging = False
        self.drag_offset = LVector2(0, 0) # Eltolás a frame központja és az egér között
        
        # 2. Ablak méretének beállítása 750x750-re
        props = WindowProperties()
        props.setSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        props.setTitle("Frame Mozgatás Kézi Ellenőrzéssel")
        self.win.requestProperties(props)
        
        # 3. Szöveg megjelenítésére szolgáló objektum létrehozása
        self.status_text = OnscreenText(
            text="Nyomd le és tartsd lenyomva az egeret a kék frame-en!",
            pos=(0, 0.9), 
            scale=0.07,   
            fg=(1, 1, 1, 1), 
            mayChange=True
        )
        
        # 4. FRAME KORDINÁTÁK KISZÁMÍTÁSA (Alapértelmezett, középső pozícióhoz)
        # Ezek az értékek a kezdeti ellenőrzéshez kellenek (pixelben, 0-tól 750-ig)
        FRAME_OFFSET = self.FRAME_SIZE / 2 # 250
        CENTER = self.WINDOW_SIZE / 2 # 375
        
        self.frame_min_x_pixel = CENTER - FRAME_OFFSET # 125
        self.frame_max_x_pixel = CENTER + FRAME_OFFSET # 625
        self.frame_min_y_pixel = CENTER - FRAME_OFFSET # 125 (Bal felsőtől)
        self.frame_max_y_pixel = CENTER + FRAME_OFFSET # 625 (Bal felsőtől)


        # 5. 500x500-as Panel (DirectFrame) Létrehozása
        panel_width_scale = 0.666 # Normált méret (-1.0-tól 1.0-ig)
        
        self.target_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.8, 0.9),  # Kék szín 
            frameSize=(-panel_width_scale, panel_width_scale, 
                       -panel_width_scale, panel_width_scale), 
            pos=(0, 0, 0), # Kezdeti pozíció (középen)
            text="500x500 Frame", 
            text_scale=0.1
        )

        # 6. Események regisztrálása a húzáshoz
        # Bal egérgomb lenyomása: Kezdi a húzási ellenőrzést
        self.accept('mouse1', self.start_drag_check)
        
        # Bal egérgomb felengedése: Leállítja a húzást
        self.accept('mouse1-up', self.stop_drag)
        
        # 7. A mozgató feladat hozzáadása, ami csak akkor fut, ha húzás van
        self.taskMgr.add(self.drag_task, 'drag_task')

    def normalize_mouse_to_pixel(self, mouse_norm):
        """Átalakítja az egér -1.0..1.0 normált koordinátáit 0..750 pixel koordinátákra."""
        mouse_x_pixel = (mouse_norm.getX() + 1) * (self.WINDOW_SIZE / 2)
        # Panda3D normált Y fordított: (-Y_norm + 1) * (WINDOW_SIZE / 2)
        mouse_y_pixel = (-mouse_norm.getY() + 1) * (self.WINDOW_SIZE / 2) 
        return mouse_x_pixel, mouse_y_pixel

    def start_drag_check(self):
        """
        Bal egérgomb lenyomásakor hívódik meg. Kézzel ellenőrzi, hogy a kattintás 
        a Frame határain belül történt-e (pixel math).
        """
        if base.mouseWatcherNode.hasMouse():
            mouse_norm = base.mouseWatcherNode.getMouse()
            mouse_x_pixel, mouse_y_pixel = self.normalize_mouse_to_pixel(mouse_norm)
            
            # 1. Kézi Ellenőrzés: Az egér pixel pozíciója a Frame pixel határain belül van-e?
            # A frame aktuális pixelhatárait ki kell számolni a normált pozíciójából
            
            # Frame aktuális normált pozíciója
            frame_pos_norm = self.target_frame.getPos()
            frame_x_norm = frame_pos_norm.getX()
            frame_y_norm = frame_pos_norm.getZ() # A Z a képernyő Y tengelye Panda3D-ben
            
            # Frame mérete normált koordinátán
            frame_half_scale = self.target_frame['frameSize'][1] # Pl. 0.666
            
            # Frame aktuális normált határai
            frame_min_x_norm = frame_x_norm - frame_half_scale
            frame_max_x_norm = frame_x_norm + frame_half_scale
            frame_min_y_norm = frame_y_norm - frame_half_scale
            frame_max_y_norm = frame_y_norm + frame_half_scale
            
            # Kézi ellenőrzés (a pozíciót a normált koordinátákkal ellenőrizzük, mert az a Frame aktuális pozíciója):
            if (frame_min_x_norm <= mouse_norm.getX() <= frame_max_x_norm and
                frame_min_y_norm <= mouse_norm.getY() <= frame_max_y_norm):
                
                # Benne van a Frame-ben
                self.is_dragging = True
                self.status_text.setText("BELEKATTINTOTT (Mozgatás)")
                
                # Eltolás kiszámítása a Frame központja és az egér között
                # Hogy a frame ne ugorjon a középpontjába, amikor elkezdjük húzni
                self.drag_offset = LVector2(
                    frame_x_norm - mouse_norm.getX(),
                    frame_y_norm - mouse_norm.getY()
                )
                self.target_frame['frameColor'] = (0.0, 0.8, 0.0, 0.9) # Zöld
                
            else:
                # Frame-en kívül
                self.is_dragging = False
                self.status_text.setText("NEM BELEKATTINTOTT")
                self.target_frame['frameColor'] = (0.8, 0.1, 0.1, 0.9) # Piros
                self.taskMgr.doMethodLater(1.5, self.reset_color_and_text, 'reset_task')
                
    def drag_task(self, task):
        """
        Folyamatosan fut, amíg az egérgomb le van nyomva (is_dragging=True), 
        és az egérhez igazítja a Frame pozícióját.
        """
        if self.is_dragging and base.mouseWatcherNode.hasMouse():
            mouse_norm = base.mouseWatcherNode.getMouse()
            
            # Új pozíció kiszámítása az eltolással
            new_x = mouse_norm.getX() + self.drag_offset.getX()
            new_y = mouse_norm.getY() + self.drag_offset.getY()
            
            # Frame pozíció beállítása. A DirectGUI a Z tengelyt használja a képernyő Y-jához.
            self.target_frame.setPos(new_x, 0, new_y)

        return Task.cont

    def stop_drag(self):
        """
        Bal egérgomb felengedésekor hívódik meg. Leállítja a húzást.
        """
        if self.is_dragging:
            self.is_dragging = False
            self.taskMgr.doMethodLater(1.5, self.reset_color_and_text, 'reset_task')

    def reset_color_and_text(self, task):
        """Visszaállítja a Frame színét és a státusz szöveget."""
        self.target_frame['frameColor'] = (0.1, 0.1, 0.8, 0.9) # Kék
        self.status_text.setText("Nyomd le és tartsd lenyomva az egeret a kék frame-en!")
        return task.done

# Az alkalmazás futtatása
app = DragApp()
app.run()