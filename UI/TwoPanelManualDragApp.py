from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, LVector2
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from direct.showbase.DirectObject import DirectObject

class TwoPanelManualDragApp(ShowBase):
    def __init__(self):
        # ShowBase inicializálása
        ShowBase.__init__(self)

        # 1. Konstansok beállítása
        self.WINDOW_SIZE = 750
        self.FRAME_SIZE = 500
        
        # Állapotjelzők húzáshoz
        self.is_dragging = False
        self.drag_offset = LVector2(0, 0) 
        self.active_frame = None # Hozzáadva: a mozgatott Frame referenciája
        
        # 2. Ablak méretének beállítása 750x750-re
        props = WindowProperties()
        props.setSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        props.setTitle("Két Frame Mozgatása Kézi Ellenőrzéssel")
        self.win.requestProperties(props)
        
        # 3. Szöveg megjelenítésére szolgáló objektum létrehozása
        self.status_text = OnscreenText(
            text="Nyomd le és tartsd lenyomva az egeret a Frame-en!",
            pos=(0, 0.9), 
            scale=0.07,   
            fg=(1, 1, 1, 1), 
            mayChange=True
        )
        
        # 4. Két Frame Létrehozása
        self.frame_list = []
        self._setup_frames()

        # 5. Események regisztrálása a húzáshoz
        self.accept('mouse1', self.start_drag_check)
        self.accept('mouse1-up', self.stop_drag)
        self.taskMgr.add(self.drag_task, 'drag_task')

    def _setup_frames(self):
        """Létrehozza a két mozgatható DirectFrame-et."""
        
        panel_width_scale = self.FRAME_SIZE / self.WINDOW_SIZE # 0.666
        
        # FRAME 1 (Kék)
        frame1 = DirectFrame(
            frameColor=(0.1, 0.1, 0.8, 0.9),
            frameSize=(-panel_width_scale, panel_width_scale, -panel_width_scale, panel_width_scale),
            pos=(-0.2, 0, -0.2), # Eltoljuk
            text="Frame 1 (500x500) - Kék", 
            text_scale=0.1
        )
        self.frame_list.append(frame1)

        # FRAME 2 (Narancs)
        frame2 = DirectFrame(
            frameColor=(0.8, 0.5, 0.1, 0.9), 
            frameSize=(-panel_width_scale, panel_width_scale, -panel_width_scale, panel_width_scale),
            pos=(0.3, 0, 0.3), # Eltoljuk
            text="Frame 2 (500x500) - Narancs", 
            text_scale=0.1
        )
        self.frame_list.append(frame2)


    def start_drag_check(self):
        """
        Bal egérgomb lenyomásakor hívódik meg. Kézzel ellenőrzi, hogy a kattintás 
        melyik Frame-en történt a normált koordináták alapján.
        """
        if base.mouseWatcherNode.hasMouse():
            mouse_norm = base.mouseWatcherNode.getMouse()
            
            # Alapértelmezett beállítások
            self.is_dragging = False
            self.active_frame = None

            # Végigmegyünk a Frame-eken fordított sorrendben (hogy a felül lévő Frame kapjon prioritást)
            for frame in reversed(self.frame_list):
                
                # Frame aktuális normált pozíciója és méretei
                frame_pos_norm = frame.getPos()
                frame_x_norm = frame_pos_norm.getX()
                frame_y_norm = frame_pos_norm.getZ() 
                frame_half_scale = frame['frameSize'][1] 
                
                frame_min_x_norm = frame_x_norm - frame_half_scale
                frame_max_x_norm = frame_x_norm + frame_half_scale
                frame_min_y_norm = frame_y_norm - frame_half_scale
                frame_max_y_norm = frame_y_norm + frame_half_scale
                
                # Kézi ellenőrzés
                if (frame_min_x_norm <= mouse_norm.getX() <= frame_max_x_norm and
                    frame_min_y_norm <= mouse_norm.getY() <= frame_max_y_norm):
                    
                    # Benne van a Frame-ben
                    self.is_dragging = True
                    self.active_frame = frame
                    
                    self.status_text.setText(f"BELEKATTINTOTT, Húzás ({self.active_frame['text']})")
                    
                    # Eltolás kiszámítása
                    self.drag_offset = LVector2(
                        frame_x_norm - mouse_norm.getX(),
                        frame_y_norm - mouse_norm.getY()
                    )
                    self.active_frame['frameColor'] = (0.0, 0.8, 0.0, 0.9) # Zöld
                    
                    # Z-sorrend frissítése: a húzott Frame kerül felülre
                    self.frame_list.remove(frame)
                    self.frame_list.append(frame)
                    frame.reparentTo(base.aspect2d)
                    
                    return # Találtunk Frame-et, leállítjuk az ellenőrzést

            # Ha a ciklus lefutott és nincs aktív Frame
            self.is_dragging = False
            self.status_text.setText("NEM BELEKATTINTOTT (Kívül)")
            self.taskMgr.doMethodLater(1.5, self.reset_color_and_text, 'reset_task')
            
    def drag_task(self, task):
        """
        Folyamatosan fut, amíg az egérgomb le van nyomva és van aktív Frame.
        """
        if self.is_dragging and self.active_frame and base.mouseWatcherNode.hasMouse():
            mouse_norm = base.mouseWatcherNode.getMouse()
            
            # Új pozíció kiszámítása az eltolással
            new_x = mouse_norm.getX() + self.drag_offset.getX()
            new_y = mouse_norm.getY() + self.drag_offset.getY()
            
            # Aktív Frame pozíció beállítása
            self.active_frame.setPos(new_x, 0, new_y)

        return Task.cont

    def stop_drag(self):
        """
        Bal egérgomb felengedésekor hívódik meg. Leállítja a húzást.
        """
        if self.is_dragging and self.active_frame:
            self.is_dragging = False
            
            # Szín visszaállítása az aktív Frame alapján
            if self.active_frame['text'].endswith("Kék"):
                self.active_frame['frameColor'] = (0.1, 0.1, 0.8, 0.9)
            else:
                self.active_frame['frameColor'] = (0.8, 0.5, 0.1, 0.9)
                
            self.active_frame = None
            self.taskMgr.doMethodLater(1.5, self.reset_color_and_text, 'reset_task')

    def reset_color_and_text(self, task):
        """Visszaállítja a státusz szöveget."""
        self.status_text.setText("Nyomd le és tartsd lenyomva az egeret a Frame-en!")
        return task.done

# Az alkalmazás futtatása
app = TwoPanelManualDragApp()
app.run()