# Mozgó Vertexek és Partikla Effektek - Panda3D Python
#
# Egy kocka 8 sarkát (vertexeit) véletlenszerűen mozgatjuk.
# Minden saroknál egy kis fehér részecske-effekt jelenik meg.

import sys
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    VBase3, VBase4, AmbientLight, PointLight, NodePath,
    TransparencyAttrib, AlphaTestAttrib, Texture, 
    # A LineSegs a dinamikus élvonal rajzoláshoz
    LineSegs, GeomNode, LVector3f, Geom # Hozzáadva Geom az explicit típusellenőrzéshez
)
import math
import random

# ----------------------------------------------------------------------
# HIBAKEZELÉS: Shader és Részecske Rendszer Importálása
# ----------------------------------------------------------------------
PARTICLES_AVAILABLE = False
try:
    from direct.particles.Particles import Particles
    from direct.particles.ParticleEffect import ParticleEffect
    from direct.particles.ParticleEmitter import ParticleEmitter
    from direct.particles.PointParticleFactory import PointParticleFactory
    from direct.particles.ColorInterpolationParticleRenderer import ColorInterpolationParticleRenderer
    # A Panda3D-nek a Texture és ColorRamp-et is tudnia kell importálni
    from panda3d.core import ColorRamp
    PARTICLES_AVAILABLE = True
except ImportError as e:
    print(f"Figyelem: Részecske modul importálási hiba: {e}. A részecske effekt nem lesz elérhető.")
    try:
        from panda3d.core import ColorRamp
    except ImportError:
        class ColorRamp:
            def __init__(self): pass
            def addComponent(self, color, value): pass
except AttributeError as e:
     print(f"Figyelem: Panda3D attribútum hiba a részecske modulokban: {e}. A részecske effekt nem lesz elérhető.")

class MovingCubeParticlesDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # ------------------------------------------------
        # 1. Alapvető beállítások
        # ------------------------------------------------
        self.set_background_color(0.1, 0.1, 0.1, 1) # Sötétszürke háttér
        self.disable_mouse()
        self.camera.set_pos(-15, -15, 10)
        self.camera.look_at(0, 0, 0)
        
        self.accept('escape', sys.exit)
        self.accept('q', sys.exit)
        print("A mozgó vertexek és a részecskék elindultak.")

        # ------------------------------------------------
        # 2. Világítás
        # ------------------------------------------------
        # Egyszerű, alacsony fényerő, hogy a fehér részecskék jól látszódjanak
        alight = AmbientLight('alight')
        alight.set_color(VBase4(0.3, 0.3, 0.3, 1))
        self.render.set_light(self.render.attach_new_node(alight))
        
        # ------------------------------------------------
        # 3. Vertex Adatok Inicializálása
        # ------------------------------------------------
        
        # Kocka sarok (vertex) kezdőpozíciók (méret: 5.0)
        s = 5.0
        initial_verts = [
            VBase3(-s, -s, -s), VBase3(s, -s, -s), VBase3(s, s, -s), VBase3(-s, s, -s),
            VBase3(-s, -s, s), VBase3(s, -s, s), VBase3(s, s, s), VBase3(-s, s, s)
        ]
        
        # A 8 vertex (sarok) adatstruktúrája
        self.vertex_data = []
        
        for i, pos in enumerate(initial_verts):
            # JAVÍTÁS: Növelt sebességtartomány a látható mozgás érdekében
            vel = LVector3f(random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0))
            
            # Minden vertexhez egy különálló részecske-effekt
            p_effect = self._create_particles(f"vertex_particle_{i}")
            if p_effect:
                p_effect.start()
            
            self.vertex_data.append({
                'pos': pos,
                'vel': vel,
                'particle_effect': p_effect,
            })
            
        # ------------------------------------------------
        # 4. Kocka Vonalak Renderelése
        # ------------------------------------------------
        
        self.cube_node = GeomNode('cube_lines')
        self.cube_np = self.render.attach_new_node(self.cube_node)
        self.cube_np.set_render_mode_thickness(3.0) # Vonalvastagság
        self.cube_np.set_color(1.0, 0.5, 0.0, 1.0) # Narancssárga szín a vonalaknak

        # Élek meghatározása (indexek a 0-7-ig terjedő vertex listában)
        self.cube_edges = [
            (0, 1), (1, 2), (2, 3), (3, 0), # Alsó lap
            (4, 5), (5, 6), (6, 7), (7, 4), # Felső lap
            (0, 4), (1, 5), (2, 6), (3, 7)  # Függőleges élek
        ]
        
        # ------------------------------------------------
        # 5. Animációs ciklus indítása
        # ------------------------------------------------
        self.taskMgr.add(self.update_cube_and_particles, "UpdateCubeTask")
        self.target_center = VBase3(0, 0, 0) # A vertexek célközéppontja
        self.max_dist = 6.0 # Maximális távolság a középponttól

        self.messenger.send('aspectRatioChanged')
        
    # ------------------------------------------------
    # 6. Animációs és Renderelési Logika
    # ------------------------------------------------

    def update_cube_and_particles(self, task):
        """Frissíti a vertex pozíciókat, a vonalakat és a részecskéket."""
        dt = globalClock.getDt()

        # Új LineSegs létrehozása (minden képkockában újra kell rajzolni)
        ls = LineSegs('cube_segments')
        ls.set_thickness(3.0)
        ls.set_color(1.0, 0.5, 0.0, 1.0) 

        for data in self.vertex_data:
            # 1. Pozíció Frissítése
            data['pos'] += data['vel'] * dt
            
            # 2. Visszajátszási/Ütközési Logika (falba ütközés a center körül)
            dist_to_center = (data['pos'] - self.target_center).length()
            if dist_to_center > self.max_dist:
                # Tükrözi a sebességet, hogy visszapattanjon
                data['vel'] = -(data['vel']) 
            
            # 3. Partikula Emitter Pozíció Frissítése
            if data['particle_effect']:
                data['particle_effect'].setPos(data['pos'])
                
        # 4. Kocka Éleinek Rajzolása
        # Az élek rajzolása a frissített pozíciók alapján
        for i, j in self.cube_edges:
            start_pos = self.vertex_data[i]['pos']
            end_pos = self.vertex_data[j]['pos']
            ls.draw_to(start_pos.x, start_pos.y, start_pos.z)
            ls.draw_to(end_pos.x, end_pos.y, end_pos.z)
            
        # 5. Renderelés: Törli a régi vonalakat és hozzáadja az újakat.
        self.cube_node.remove_all_geoms() 
        
        new_geom = ls.create()
        final_geom = None
        
        # 5a. A tényleges Geom objektum kinyerése (GeomNode-ból vagy Geom-ként)
        if isinstance(new_geom, GeomNode):
            if new_geom.get_num_geoms() > 0:
                final_geom = new_geom.get_geom(0)
        elif isinstance(new_geom, Geom):
            final_geom = new_geom
        else:
            # Ha a LineSegs.create() sem Geom, sem GeomNode-ot nem ad vissza
            return Task.cont 

        # 5b. MÁSOTLAT KÉSZÍTÉSE ÉS HOZZÁADÁSA (A const hiba elkerülése végett)
        if final_geom:
            try:
                # Ezt a másolatot kéri a GeomNode.add_geom() a legtöbb környezetben
                mutable_geom = final_geom.make_copy()
                self.cube_node.add_geom(mutable_geom)
            except AttributeError:
                # Ha make_copy() hiányzik (ritka), megpróbáljuk a const objektumot hozzáadni.
                self.cube_node.add_geom(final_geom)
                print("Figyelem: Nem sikerült másolatot készíteni a Geom-ról, const objektumot használunk.")

        return Task.cont

    # ------------------------------------------------
    # 7. Segéd Függvények (Partikla generátor)
    # ------------------------------------------------

    def _create_particles(self, name):
        """Partikla effekt létrehozása egy vertexhez."""
        
        if not PARTICLES_AVAILABLE:
            return None # Partikula rendszer nem elérhető
            
        p = ParticleEffect(name)
        p.setRenderParent(self.render) # Globális render parent
        p.setSystemLifespan(0.0) # Végtelen élettartam
        
        # Konfigurálja az 'Particles' objektumot
        particles = Particles()
        particles.setRenderParent(self.render) 
        particles.setPoolSize(100)
        particles.setBirthRate(0.05) # Lassú és állandó kibocsátás

        # 1. Textúra létrehozása (1x1 fehér pont)
        p_texture = Texture()
        p_texture.setup_2d_texture(1, 1, Texture.T_unsigned_byte, Texture.F_rgba)
        p_texture.setRamImage(b'\xff\xff\xff\xff') # Fehér (R, G, B, A = 255, 255, 255, 255)

        # 2. Renderer beállítása (Color Interpolation)
        renderer = ColorInterpolationParticleRenderer()
        renderer.setUserAlpha(1.0)
        renderer.setTexture(p_texture) 
        
        # Színátmenet: Fehér -> Fekete (elhalványulás)
        color_ramp = ColorRamp() 
        color_ramp.addComponent(VBase4(1.0, 1.0, 1.0, 1.0), 0.0) # Fehér
        color_ramp.addComponent(VBase4(1.0, 1.0, 1.0, 0.5), 0.5) # Fehér/Szürke (átlátszó)
        color_ramp.addComponent(VBase4(0.0, 0.0, 0.0, 0.0), 1.0) # Fekete (teljesen átlátszó)
        renderer.setColorRamp(color_ramp)
        
        renderer.setXScaleFlag(True)
        renderer.setYScaleFlag(True)
        renderer.setInitialXScale(0.3)
        renderer.setFinalXScale(0.1)
        renderer.setInitialYScale(0.3)
        renderer.setFinalYScale(0.1)
        
        particles.setRenderer(renderer)
        particles.setAttrib(TransparencyAttrib.make(TransparencyAttrib.M_alpha)) # Blending engedélyezése
        
        # Factory beállítása (Részecskék tulajdonságai)
        factory = PointParticleFactory()
        factory.setLifespanBase(0.8) # Rövid élettartam
        factory.setLifespanSpread(0.2)
        
        # Emitter beállítása (Honnan sugároz)
        emitter = ParticleEmitter()
        emitter.setEmissionType(emitter.ET_sphere) # Gömb alakú kibocsátás
        emitter.setAmplitudeSpread(0.5)
        emitter.setRadius(0.5) # Kis gömb a sarok körül
        emitter.setExplicitLaunchVector(VBase4(0.0, 0.0, 0.0, 0.0))
        emitter.setLaunchAngle(emitter.LAV_up)
        emitter.setLaunchBand(10.0)
        emitter.setEmissionVolume(emitter.EV_sphere)
        
        particles.setFactory(factory)
        particles.setEmitter(emitter)
        p.addParticles(particles)
        
        return p


demo = MovingCubeParticlesDemo()
demo.run()