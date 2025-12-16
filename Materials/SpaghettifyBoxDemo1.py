# Spagettizálódó Kocka Demó - Panda3D Python
#
# Egy kocka függőlegesen nyúlik (Z-tengelyen), miközben színe
# vörösről feketére halványul a "spagettizálódás" illúzióját keltve.

import sys
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    Shader, VBase4, GeomVertexData, GeomVertexFormat, GeomVertexWriter, 
    GeomTriangles, GeomNode, NodePath, Geom, AmbientLight, PointLight
)
import math 

class SpaghettifyBoxDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # ------------------------------------------------
        # 1. Alapvető beállítások
        # ------------------------------------------------
        self.set_background_color(0, 0, 0, 1)  # Fekete háttér
        self.disable_mouse()
        self.camera.set_pos(-10, -10, 5) # Kamera, ami jól látja a függőleges nyúlást
        self.camera.look_at(0, 0, 0)
        
        # Billentyűzet vezérlés hozzáadása
        self.accept('escape', sys.exit)
        self.accept('q', sys.exit)
        self.accept('space', self.reset_animation)
        print("Nyomja meg a SPACE-t az animáció újraindításához.")


        # ------------------------------------------------
        # 2. Shader Kód (Színátmenet vezérlése)
        # ------------------------------------------------

        # Vertex Shader (Egyszerű transzformáció)
        vertex_shader = """
        #version 130
        uniform mat4 p3d_ModelViewProjectionMatrix;
        in vec4 p3d_Vertex;
        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        }
        """

        # Fragment Shader (A vörös szín intenzitását a RedIntensity uniform vezérli)
        fragment_shader = """
        #version 130
        uniform float RedIntensity; // 1.0 = Vörös, 0.0 = Fekete
        out vec4 fragColor;
        
        void main() {
            // A szín vörösből (RedIntensity=1) feketébe (RedIntensity=0) halványul
            fragColor = vec4(RedIntensity, 0.0, 0.0, 1.0);
        }
        """

        # Shader létrehozása
        self.spaghetti_shader = self._create_shader(vertex_shader, fragment_shader)

        
        # ------------------------------------------------
        # 3. Világítás és Helyszín beállítás
        # ------------------------------------------------
        
        # Ambient fény (nagyon kicsi, hogy kiemelje a kontrasztot)
        ambient_light = AmbientLight('ambientLight')
        ambient_light.set_color(VBase4(0.05, 0.05, 0.05, 1))
        alnp = self.render.attach_new_node(ambient_light)
        self.render.set_light(alnp)

        # Helyszíni fény (opcionális, de jó ha van egy normál fényforrás is)
        plight = PointLight('plight')
        plight.set_color(VBase4(0.5, 0.5, 0.5, 1))
        plnp = self.render.attach_new_node(plight)
        plnp.set_pos(-5, -5, 5)
        self.render.set_light(plnp)


        # ------------------------------------------------
        # 4. Objektum létrehozása és animáció beállítása
        # ------------------------------------------------
        
        # A spagettizálódó kocka/rúd (Alapméret: 2x2x2)
        initial_size = 2.0
        self.box_geom = self._create_cuboid_mesh("spaghetti_box", initial_size, initial_size, initial_size)
        self.box_np = NodePath(self.box_geom)
        self.box_np.reparent_to(self.render)
        self.box_np.set_pos(0, 0, initial_size / 2.0) # Középre igazítás Z-ben
        
        if self.spaghetti_shader:
            self.box_np.set_shader(self.spaghetti_shader)
            self.box_np.set_shader_input("RedIntensity", 1.0) # Kezdeti szín: Vörös
        else:
            self.box_np.set_color(1.0, 0.0, 0.0, 1.0)

        # Animációs változók
        self.current_stretch = 1.0
        self.max_stretch = 20.0
        self.stretch_speed = 4.0

        # Animációs ciklus indítása
        self.taskMgr.add(self.spaghettify_task, "SpaghettifyTask")

        self.messenger.send('aspectRatioChanged')
        
    # ------------------------------------------------
    # 5. Animációs logika
    # ------------------------------------------------

    def spaghettify_task(self, task):
        """Kezeli a nyúlást és a szín halványítását."""
        dt = globalClock.getDt()

        # 1. Nyújtás/Visszaállás
        self.current_stretch += self.stretch_speed * dt
        
        if self.current_stretch >= self.max_stretch:
            self.current_stretch = self.max_stretch
            # Az animáció befejezésekor megállítjuk a task-ot, amíg újra nem indítjuk
            return Task.done
        
        # Skála alkalmazása (csak Z tengelyen)
        self.box_np.set_scale(1.0, 1.0, self.current_stretch)
        # Középre igazítás (hogy felfelé nyúljon a talajtól)
        self.box_np.set_z(self.current_stretch / 2.0) 

        # 2. Szín Halványítása (Vörösről Feketére)
        # 0.0 (kezdeti nyúlás) és 1.0 (maximális nyúlás) közötti normalizált érték
        normalized_stretch = (self.current_stretch - 1.0) / (self.max_stretch - 1.0)
        
        # A vörös intenzitás csökken, ahogy a nyúlás nő (1.0 -> 0.0)
        red_intensity = max(0.0, 1.0 - normalized_stretch) 
        
        if self.spaghetti_shader:
            self.box_np.set_shader_input("RedIntensity", red_intensity)

        return Task.cont

    def reset_animation(self):
        """Visszaállítja a kockát az eredeti állapotába és újraindítja az animációt."""
        self.current_stretch = 1.0
        self.box_np.set_scale(1.0, 1.0, self.current_stretch)
        self.box_np.set_z(self.box_np.get_scale()[2] / 2.0)
        if self.spaghetti_shader:
            self.box_np.set_shader_input("RedIntensity", 1.0)
        
        # Újraindítja a task-ot, ha már befejeződött
        if not self.taskMgr.hasTaskNamed("SpaghettifyTask"):
             self.taskMgr.add(self.spaghettify_task, "SpaghettifyTask")
             
    # ------------------------------------------------
    # 6. Segéd függvények (Shader és Mesh generátor)
    # ------------------------------------------------

    def _create_shader(self, vertex_s, fragment_s):
        """Kezeli a Panda3D verziókon keresztüli shader létrehozási hibákat."""
        shader = None
        try:
            # Modern Panda3D (Shader.make és Shader.L_glsl)
            shader = Shader.make(
                Shader.L_glsl,
                vertex_s,
                fragment_s
            )
        except AttributeError:
            try:
                # Visszaesés a régebbi SL_GLSL konstansra
                from panda3d.core import SL_GLSL
                shader = Shader.load_source(SL_GLSL, vertex_s, fragment_s)
            except (AttributeError, ImportError) as e:
                print(f"HIBA: A shader konstansai ('L_glsl'/'SL_GLSL') nem elérhetők. Hiba: {e}")
                shader = None
        except Exception as e:
            print(f"Általános HIBA a shader betöltése során: {e}")
            shader = None
        return shader

    def _create_cuboid_mesh(self, name, x_size, y_size, z_size):
        """Téglatest mesh generálása egyedi méretekkel (X, Y, Z)."""
        format = GeomVertexFormat.get_v3n3() # pozíció és normál
        vdata = GeomVertexData(name, format, Geom.UHDynamic)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        
        sx, sy, sz = x_size / 2.0, y_size / 2.0, z_size / 2.0
        
        # A téglatest vertexei
        verts = [
            (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), # Alsó lap
            (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)    # Felső lap
        ]
        
        # Lapok (indexek) és normálok
        faces = [
            (0, 3, 2, 0, 2, 1, (0, 0, -1)), # Alsó
            (4, 5, 6, 4, 6, 7, (0, 0, 1)),  # Felső
            (0, 4, 7, 0, 7, 3, (-1, 0, 0)), # Bal
            (1, 2, 6, 1, 6, 5, (1, 0, 0)),  # Jobb
            (0, 1, 5, 0, 5, 4, (0, -1, 0)), # Hátsó
            (3, 7, 6, 3, 6, 2, (0, 1, 0))   # Első
        ]

        prim = GeomTriangles(Geom.UHDynamic)
        
        vdata_index = 0
        for face in faces:
            for i in face[:6]:
                vertex.add_data3f(verts[i])
                normal.add_data3f(face[6]) 
                prim.add_vertex(vdata_index)
                vdata_index += 1

        geom = Geom(vdata)
        geom.add_primitive(prim)
        
        node = GeomNode(name)
        node.add_geom(geom)
        return node


demo = SpaghettifyBoxDemo()
demo.run()