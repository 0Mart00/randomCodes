# Fénycsík (Glow) Material Demo - Panda3D Python
#
# Ez a script egy egyszerű GLSL shadert használ, hogy egy objektumot
# sugárzóan fényes, "fénycsík" forrásként mutasson be a Panda3D-ben.
# A modelleket belsőleg generáljuk (meshként) az OSError elkerülése érdekében.

import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    Shader, PointLight, VBase4, AmbientLight, 
    GeomVertexData, GeomVertexFormat, GeomVertexWriter, 
    GeomTriangles, GeomNode, NodePath, Geom
)
# A numpy importot eltávolítom, mivel nem volt használva a mesh generátorokban
import math 

class GlowMaterialDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # ------------------------------------------------
        # 0. Geometria Generálása (Mesh-ek)
        # ------------------------------------------------
        # Létrehozzuk a SUGÁRZÓ RUDAT (fénycsík material)
        # Méret: 0.5 széles, 0.5 magas, 6.0 hosszú (Y tengelyen)
        self.glow_rod = self._create_cuboid_mesh("glow_rod_mesh", 0.5, 0.5, 6.0)
        
        # Létrehozzuk a NORMÁL OBJEKTUMOT (Gömb)
        self.normal_sphere = self._create_sphere_mesh("normal_sphere_mesh", 1.5, 30)


        # ------------------------------------------------
        # 1. Alapvető beállítások
        # ------------------------------------------------
        self.set_background_color(0, 0, 0, 1)  # Fekete háttér
        self.disable_mouse()
        self.camera.set_pos(-8, -10, 3) # Kamera pozíció módosítva a rúdhoz
        self.camera.look_at(0, 0, 0)
        
        # Billentyűzet vezérlés hozzáadása a kilépéshez
        self.accept('escape', sys.exit)
        self.accept('q', sys.exit)

        # ------------------------------------------------
        # 2. GLSL Shader Kód
        # ------------------------------------------------

        # Vertex Shader (Egyszerű transzformáció)
        vertex_shader = """
        #version 130
        
        // A Panda3D beépített Mátrixai
        uniform mat4 p3d_ModelViewProjectionMatrix;
        uniform mat4 p3d_ModelViewMatrix; // Szükséges lehet a normálokhoz
        
        // A Panda3D beépített vertex attribútum
        in vec4 p3d_Vertex;
        
        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        }
        """

        # Fragment Shader (Egyszerű "Glow" material)
        fragment_shader = """
        #version 130
        
        // Uniform változó a material sugárzó színének beállításához
        uniform vec4 glowColor;
        
        // Kimenet a frame buffer-be
        out vec4 fragColor;
        
        void main() {
            // Ezzel a shaderrel az objektum egyszerűen a 'glowColor' színt sugározza,
            // figyelmen kívül hagyva a normál világítást.
            fragColor = glowColor;
        }
        """

        # Shader létrehozása
        self.glow_shader = None
        try:
            # 1. kísérlet: Modern Panda3D (Shader.make és Shader.L_glsl)
            self.glow_shader = Shader.make(
                Shader.L_glsl,
                vertex_shader,
                fragment_shader
            )
            print("Shader betöltve a modern (L_glsl) módszerrel.")
        except AttributeError:
            # Ha az L_glsl nem érhető el, próbáljuk meg a régebbi load_source metódust
            print("Figyelem: Az 'Shader.L_glsl' konstans nem található. Visszaesés a régebbi betöltési módszerre...")
            try:
                # Kísérlet a régebbi SL_GLSL konstans betöltésére
                from panda3d.core import SL_GLSL
                self.glow_shader = Shader.load_source(SL_GLSL, vertex_shader, fragment_shader)
                print("Shader betöltve a régebbi (SL_GLSL) módszerrel.")
            except (AttributeError, ImportError) as e:
                # Kezeljük a felhasználó által jelentett ImportError-t is
                print(f"Súlyos HIBA: A Panda3D shader konstansai ('L_glsl'/'SL_GLSL') nem érhetők el a dinamikus betöltéshez. A shader nem lesz alkalmazva. Hiba: {e}")
                self.glow_shader = None
        except Exception as e:
            # Minden más hiba (pl. shader fordítási hiba)
            print(f"Általános HIBA a shader betöltése során: {e}")
            self.glow_shader = None

        
        # ------------------------------------------------
        # 3. Világítás (Hogy a nem-glow objektumok látszódjanak)
        # ------------------------------------------------
        
        # Egy egyszerű PointLight hozzáadása a környezet megvilágításához
        plight = PointLight('plight')
        plight.set_color(VBase4(0.8, 0.8, 0.8, 1))
        plnp = self.render.attach_new_node(plight)
        plnp.set_pos(5, -10, 8)
        self.render.set_light(plnp)
        
        # Ambient fény a sötét sarkok elkerülésére 
        ambient_light = AmbientLight('ambientLight')
        ambient_light.set_color(VBase4(0.1, 0.1, 0.1, 1)) # Kicsit sötétebbre véve, hogy a fénylő rúd jobban kitűnjön
        alnp = self.render.attach_new_node(ambient_light)
        self.render.set_light(alnp)


        # ------------------------------------------------
        # 4. Objektumok elhelyezése és material alkalmazása
        # ------------------------------------------------
        
        # FÉNY RÚD OBJEKTUM - Fénycsík material
        glow_rod_np = NodePath(self.glow_rod)
        glow_rod_np.reparent_to(self.render)
        glow_rod_np.set_pos(-3, 0, 0) # Elhelyezzük balra
        glow_rod_np.set_hpr(90, 0, 0) # Elforgatjuk az X tengelyen álló helyzetbe

        # Shader alkalmazása az objektumra
        if self.glow_shader:
            glow_rod_np.set_shader(self.glow_shader)
            # A 'glowColor' uniform beállítása (pl. egy erős zöld fény)
            glow_rod_np.set_shader_input("glowColor", VBase4(0.1, 1.0, 0.1, 1.0))
        else:
            print("Figyelem: A sugárzó material nem töltődött be. A rúd csak sima zöld lesz.")
            glow_rod_np.set_color(0.1, 1.0, 0.1, 1.0) 

        # EGY MÁSIK OBJEKTUM - Normál világítással (Gömb)
        
        normal_sphere_np = NodePath(self.normal_sphere)
        normal_sphere_np.reparent_to(self.render)
        normal_sphere_np.set_pos(3, 0, 0) # Elhelyezzük jobbra
        
        # Állítsunk be neki egy színt
        normal_sphere_np.set_color(1, 0.3, 0.3, 1) # Pirosas szín
        
        self.messenger.send('aspectRatioChanged')
        
    # ------------------------------------------------
    # 5. Geometria Generáló Függvények
    # ------------------------------------------------

    def _create_cuboid_mesh(self, name, x_size, y_size, z_size):
        """Téglatest (rúd) mesh generálása egyedi méretekkel (X, Y, Z)."""
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
        
        # Téglatest lapok (indexek) - Minden lap 2 háromszög (6 index)
        # Normálok beállítása a lapokhoz
        faces = [
            # Z-negatív (Alsó)
            (0, 3, 2, 0, 2, 1, (0, 0, -1)),
            # Z-pozitív (Felső)
            (4, 5, 6, 4, 6, 7, (0, 0, 1)),
            # X-negatív (Bal)
            (0, 4, 7, 0, 7, 3, (-1, 0, 0)),
            # X-pozitív (Jobb)
            (1, 2, 6, 1, 6, 5, (1, 0, 0)),
            # Y-negatív (Hátsó)
            (0, 1, 5, 0, 5, 4, (0, -1, 0)),
            # Y-pozitív (Első)
            (3, 7, 6, 3, 6, 2, (0, 1, 0))
        ]

        prim = GeomTriangles(Geom.UHDynamic)
        
        # A GeoemVertexData-nak a lapok indexeinek megfelelő vertexeket és normálokat adjuk
        vdata_index = 0
        for face in faces:
            # Vertex pozíciók
            for i in face[:6]:
                vertex.add_data3f(verts[i])
                normal.add_data3f(face[6]) # A normál a laphoz
                prim.add_vertex(vdata_index)
                vdata_index += 1

        geom = Geom(vdata)
        geom.add_primitive(prim)
        
        node = GeomNode(name)
        node.add_geom(geom)
        return node
        
    def _create_sphere_mesh(self, name, radius, resolution):
        """Gömb mesh generálása (UV-mapping alapján)"""
        format = GeomVertexFormat.get_v3n3()
        vdata = GeomVertexData(name, format, Geom.UHDynamic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        
        prim = GeomTriangles(Geom.UHDynamic)
        
        # A gömb pontjainak generálása
        vertices = []
        for i in range(resolution + 1):
            lat = math.pi * i / resolution
            for j in range(resolution + 1):
                lon = 2 * math.pi * j / resolution
                x = radius * math.sin(lat) * math.cos(lon)
                y = radius * math.sin(lat) * math.sin(lon)
                z = radius * math.cos(lat)
                
                vertex.add_data3f(x, y, z)
                
                # A normál megegyezik a normalizált pozícióval (gömb esetén)
                nx, ny, nz = x / radius, y / radius, z / radius
                normal.add_data3f(nx, ny, nz)
                vertices.append((x, y, z))

        # Háromszögek generálása
        v_idx = 0
        for i in range(resolution):
            for j in range(resolution):
                p1 = i * (resolution + 1) + j
                p2 = i * (resolution + 1) + j + 1
                p3 = (i + 1) * (resolution + 1) + j
                p4 = (i + 1) * (resolution + 1) + j + 1

                # Első háromszög
                prim.add_vertex(p1)
                prim.add_vertex(p3)
                prim.add_vertex(p2)
                
                # Második háromszög
                prim.add_vertex(p2)
                prim.add_vertex(p3)
                prim.add_vertex(p4)

        geom = Geom(vdata)
        geom.add_primitive(prim)
        
        node = GeomNode(name)
        node.add_geom(geom)
        return node


demo = GlowMaterialDemo()
demo.run()