from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, LVector2, MouseButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
import math # Szükség lehet matematikai számításokhoz

class ManualClickApp(ShowBase):
    def __init__(self):
        # ShowBase inicializálása
        ShowBase.__init__(self)

        # 1. Konstansok beállítása
        self.WINDOW_SIZE = 750
        self.FRAME_SIZE = 500
        
        # 2. Ablak méretének beállítása 750x750-re
        props = WindowProperties()
        props.setSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        props.setTitle("Kézi Koordináta Ellenőrzés")
        self.win.requestProperties(props)
        
        # 3. Szöveg megjelenítésére szolgáló objektum létrehozása
        self.status_text = OnscreenText(
            text="Kattints az ablakba!",
            pos=(0, 0.9), 
            scale=0.07,   
            fg=(1, 1, 1, 1), 
            mayChange=True
        )
        
        # 4. FRAME KORDINÁTÁK KISZÁMÍTÁSA PIXELBEN (Függőlegesen inverz)
        # Panda3D: (0,0) a bal alsó sarok. A GUI rendszer a bal felső sarkot használja.
        
        # Mivel a Frame középen (0,0) van, a szélei a 750-es ablakban:
        # A középpont koordinátái: (750 / 2, 750 / 2) = (375, 375)
        
        FRAME_OFFSET = self.FRAME_SIZE / 2 # 250
        CENTER = self.WINDOW_SIZE / 2 # 375
        
        # Koordináták a Panda3D (bal alsó) 2D rendszerében:
        self.frame_min_x = CENTER - FRAME_OFFSET # 375 - 250 = 125
        self.frame_max_x = CENTER + FRAME_OFFSET # 375 + 250 = 625
        
        # A Y tengelyt fordítva kell kezelni, ha a Panda3D 2D-s koordináta rendszere (bal alsó)
        # és az egér kurzorának (bal felső) Y tengelyét használjuk.
        # A DirectGUI azonban a bal felső sarkot használja (0,0), így egyszerűbb, ha a Y tengelyt is a bal felsőtől számoljuk:
        
        self.frame_min_y = CENTER - FRAME_OFFSET # 125 (Bal felső: 0-tól)
        self.frame_max_y = CENTER + FRAME_OFFSET # 625 (Bal felső: 0-tól)

        # 5. 500x500-as Panel (DirectFrame) Létrehozása VIZUÁLIS SEGÉDLETNEK
        panel_width_scale = 0.666 
        self.target_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.8, 0.9),  # Kék szín 
            frameSize=(-panel_width_scale, panel_width_scale, 
                       -panel_width_scale, panel_width_scale), 
            pos=(0, 0, 0),
            text="Frame: X: 125-625, Y: 125-625", 
            text_scale=0.05
        )

        # 6. Esemény regisztrálása a kattintásra
        # A 'mouse1' eseményre hívódik meg a manuális ellenőrzés
        self.accept('mouse1', self.check_click_position)
        
        # 7. Információ kiírása a konzolra
        self.log_frame_positions()

    def log_frame_positions(self):
        """Kiírja a frame pozícióit a konzolra ellenőrzés céljából."""
        print("--- FRAME POZÍCIÓK (Pixel) ---")
        print(f"Ablak mérete: {self.WINDOW_SIZE}x{self.WINDOW_SIZE}")
        print(f"Frame X minimális: {self.frame_min_x}")
        print(f"Frame X maximális: {self.frame_max_x}")
        print(f"Frame Y minimális: {self.frame_min_y} (Bal felsőtől)")
        print(f"Frame Y maximális: {self.frame_max_y} (Bal felsőtől)")
        print("-------------------------------")


    def check_click_position(self):
        """
        Kiolvassa az egér pozícióját és kézzel ellenőrzi, hogy a Frame-ben van-e.
        """
        # Ellenőrizzük, hogy az egér aktív-e és elérhető-e a pozíció
        if base.mouseWatcherNode.hasMouse():
            # Lekérjük az egér normált (scaled) koordinátáit (-1-től 1-ig)
            mouse_norm = base.mouseWatcherNode.getMouse() 
            
            # Átalakítjuk a normált koordinátákat pixel koordinátákra (0-tól 750-ig)
            # X: (normált_x + 1) * (WINDOW_SIZE / 2)
            mouse_x_pixel = (mouse_norm.getX() + 1) * (self.WINDOW_SIZE / 2)
            
            # Y: A Panda3D normált Y koordinátája alulról felfelé nő (-1-től 1-ig).
            # Pixel Y koordinátát a bal felső saroktól számoljuk:
            mouse_y_pixel = (-mouse_norm.getY() + 1) * (self.WINDOW_SIZE / 2) 

            # A 3D-s motor egér Y-ja pont a fordítottja a 2D-s GUI egér Y-jának.
            # Tehát a pixel y-t: (1 - normalizált_y) * (WINDOW_SIZE / 2)

            print(f"Kattintás pozíciója (Pixel): X={mouse_x_pixel:.2f}, Y={mouse_y_pixel:.2f}")

            # KÉZI IF FELTÉTEL ELLENŐRZÉSE
            # Ellenőrzi, hogy az egér koordinátái a Frame (125, 125) és (625, 625) között vannak-e
            
            if (self.frame_min_x <= mouse_x_pixel <= self.frame_max_x and
                self.frame_min_y <= mouse_y_pixel <= self.frame_max_y):
                
                # Frame-en belül
                self.status_text.setText("BELEKATTINTOTT")
                print("BELEKATTINTOTT (Frame-en belül)")
                self.target_frame['frameColor'] = (0.0, 0.8, 0.0, 0.9) # Zöld
                self.taskMgr.doMethodLater(1.5, self.reset_color_and_text, 'reset_task')
                
            else:
                # Frame-en kívül
                self.status_text.setText("NEM BELEKATTINTOTT")
                print("NEM BELEKATTINTOTT (Frame-en kívül)")
                self.target_frame['frameColor'] = (0.8, 0.1, 0.1, 0.9) # Piros
                self.taskMgr.doMethodLater(1.5, self.reset_color_and_text, 'reset_task')

    def reset_color_and_text(self, task):
        """Visszaállítja a Frame színét és a státusz szöveget."""
        self.target_frame['frameColor'] = (0.1, 0.1, 0.8, 0.9) # Kék
        self.status_text.setText("Kattints az ablakba!")
        return task.done

# Az alkalmazás futtatása
app = ManualClickApp()
app.run()